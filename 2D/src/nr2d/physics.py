"""Small-strain plane-strain FEM with two Maxwell branches and circular contact.

Body equilibrium is quasistatic. The tool has one dynamic indentation coordinate.
Contact uses a frictionless circular lower surface and two Gauss points per top edge.
Positive indentation moves the tool down. SI units throughout.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve


@dataclass(frozen=True)
class Config:
    nx: int = 24
    ny: int = 12
    width: float = 0.04
    height: float = 0.02
    thickness: float = 0.01
    radius: float = 0.03
    E_inf: float = 20000.0
    E_fast: float = 40000.0
    E_slow: float = 60000.0
    nu: float = 0.35
    tau_fast: float = 0.12
    tau_slow: float = 0.9
    tool_mass: float = 0.04
    actuator_k: float = 5000.0
    actuator_c: float = 12.0
    penalty: float = 2.0e9
    dt: float = 0.01
    clearance: float = 0.00015
    newton_tol: float = 1.0e-8
    newton_max: int = 35

    def asdict(self):
        return asdict(self)


@dataclass
class State:
    u: np.ndarray
    z: np.ndarray
    d: float
    v: float = 0.0
    t: float = 0.0

    def copy(self):
        return State(self.u.copy(), self.z.copy(), float(self.d), float(self.v), float(self.t))


@dataclass
class Trace:
    config: dict
    time: np.ndarray
    command: np.ndarray
    phase: np.ndarray
    u: np.ndarray
    z: np.ndarray
    d: np.ndarray
    v: np.ndarray
    force: np.ndarray
    markers: np.ndarray
    diagnostics: np.ndarray
    wall_seconds: float
    metadata: dict = field(default_factory=dict)

    def checkpoint(self, index=-1):
        return State(self.u[index].copy(), self.z[index].copy(), float(self.d[index]),
                     float(self.v[index]), float(self.time[index]))

    @property
    def observation(self):
        return np.column_stack((self.d, self.v, self.force, self.markers))

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {key: getattr(self, key) for key in
                  ("time", "command", "phase", "u", "z", "d", "v", "force", "markers", "diagnostics")}
        np.savez_compressed(path, **arrays, header=json.dumps({"config": self.config,
                            "wall_seconds": self.wall_seconds, "metadata": self.metadata}))

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            header = json.loads(str(data["header"]))
            return cls(**header, **{k: data[k] for k in data.files if k != "header"})


class SpatialModel:
    def __init__(self, config: Config = Config()):
        self.c = config
        c = config
        if not (c.nx >= 4 and c.ny >= 2 and 0 < c.nu < 0.49 and c.radius > c.width / 2):
            raise ValueError("Invalid mesh, Poisson ratio or tool radius")
        xx, yy = np.meshgrid(np.linspace(-c.width/2, c.width/2, c.nx+1),
                             np.linspace(0, c.height, c.ny+1))
        self.nodes = np.column_stack((xx.ravel(), yy.ravel()))
        triangles = []
        for j in range(c.ny):
            for i in range(c.nx):
                a = j*(c.nx+1)+i
                b, d, e = a+1, a+c.nx+1, a+c.nx+2
                # Alternating diagonals avoid a preferred global shear direction.
                triangles.extend(((a,b,e),(a,e,d)) if (i+j)%2 == 0 else ((a,b,d),(b,e,d)))
        self.tri = np.array(triangles, dtype=int)
        xy = self.nodes[self.tri]
        x, y = xy[:,:,0], xy[:,:,1]
        area2 = (x[:,1]-x[:,0])*(y[:,2]-y[:,0])-(x[:,2]-x[:,0])*(y[:,1]-y[:,0])
        self.area = area2/2
        b = np.column_stack((y[:,1]-y[:,2],y[:,2]-y[:,0],y[:,0]-y[:,1]))/area2[:,None]
        g = np.column_stack((x[:,2]-x[:,1],x[:,0]-x[:,2],x[:,1]-x[:,0]))/area2[:,None]
        self.B = np.zeros((len(self.tri),3,6))
        self.B[:,0,::2], self.B[:,1,1::2] = b, g
        self.B[:,2,::2], self.B[:,2,1::2] = g, b
        self.dofs = np.stack((2*self.tri,2*self.tri+1),axis=-1).reshape(-1,6)
        self.nd = len(self.nodes)*2
        self.fixed = np.arange(2*(c.nx+1))
        self.free = np.arange(2*(c.nx+1),self.nd)
        nu = c.nu
        self.D = np.array([[1-nu,nu,0],[nu,1-nu,0],[0,0,(1-2*nu)/2]])/((1+nu)*(1-2*nu))
        ke = np.einsum("eai,ab,ebj,e->eij", self.B,self.D,self.B,self.area*c.thickness)
        rows = np.repeat(self.dofs,6,axis=1).ravel()
        cols = np.tile(self.dofs,(1,6)).ravel()
        self.Kunit = sparse.coo_matrix((ke.ravel(),(rows,cols)),shape=(self.nd,self.nd)).tocsc()
        self.top = np.arange(c.ny*(c.nx+1),(c.ny+1)*(c.nx+1))
        self.edge_nodes = np.repeat(np.column_stack((self.top[:-1],self.top[1:])),2,axis=0)
        xi = np.tile(np.array([-1,1])/np.sqrt(3),c.nx)
        self.N = np.column_stack(((1-xi)/2,(1+xi)/2))
        self.qweight = np.full(2*c.nx,c.width/c.nx/2*c.thickness)
        self.qref = np.einsum("qi,qij->qj",self.N,self.nodes[self.edge_nodes])
        self.marker_nodes = np.array([round(c.ny*.65)*(c.nx+1),round(c.ny*.65)*(c.nx+1)+c.nx])
        self.marker_sign = np.array([-1.,1.])
        self.Ebranch = np.array([c.E_fast,c.E_slow])
        self.tau = np.array([c.tau_fast,c.tau_slow])
        self._bulk = {}

    def initial(self):
        return State(np.zeros(self.nd), np.zeros((2,len(self.tri),3)), -self.c.clearance)

    def strain(self,u):
        return np.einsum("eij,ej->ei",self.B,u[self.dofs])

    def assemble_stress(self,stress):
        local = np.einsum("eai,ea,e->ei",self.B,stress,self.area*self.c.thickness)
        out = np.zeros(self.nd)
        np.add.at(out,self.dofs.ravel(),local.ravel())
        return out

    def contact(self,u,d):
        points = self.qref + np.einsum("qi,qij->qj",self.N,u.reshape(-1,2)[self.edge_nodes])
        x = points[:,0]
        if np.max(np.abs(x)) >= self.c.radius:
            raise RuntimeError("Contact surface left the valid circular arc")
        root = np.sqrt(self.c.radius**2-x*x)
        sag = self.c.radius-root
        gap = points[:,1]-self.c.height+d-sag
        active = gap > 0
        pressure = self.c.penalty*np.maximum(gap,0)
        # Gradient of vertical gap; equivalent to a normal contact force with
        # the corresponding projected pressure measure. Not vertical-only contact.
        n = np.column_stack((-x/root,np.ones_like(x)))
        row = np.repeat(np.arange(len(gap)),5)
        col = np.column_stack((2*self.edge_nodes[:,0],2*self.edge_nodes[:,0]+1,
                               2*self.edge_nodes[:,1],2*self.edge_nodes[:,1]+1,
                               np.full(len(gap),self.nd))).ravel()
        val = np.column_stack((self.N[:,0,None]*n,self.N[:,1,None]*n,np.ones(len(gap)))).ravel()
        G = sparse.coo_matrix((val,(row,col)),shape=(len(gap),self.nd+1)).tocsr()
        residual = np.asarray(G.T@(pressure*self.qweight)).ravel()
        tangent = G.T@sparse.diags(self.c.penalty*self.qweight*active)@G
        return residual,tangent,float(np.sum(pressure*self.qweight)),gap,points,pressure

    def equilibrate(self,z,d,u_guess=None):
        """Instant equilibrium with a prescribed tool coordinate and unchanged memory."""
        c = self.c
        memory = np.einsum("i,ab,ieb->ea",self.Ebranch,self.D,z)
        rhs = self.assemble_stress(memory)
        K = (c.E_inf+sum(self.Ebranch))*self.Kunit
        u = np.zeros(self.nd) if u_guess is None else u_guess.copy()
        for _ in range(c.newton_max):
            contact,J,*_ = self.contact(u,d)
            residual = K@u-rhs+contact[:-1]
            if np.max(np.abs(residual[self.free])) < c.newton_tol:
                return u
            mat=(K+J[:-1,:-1]).tocsc()[self.free,:][:,self.free]
            u[self.free] -= spsolve(mat,residual[self.free])
        raise RuntimeError("Instant equilibrium did not converge")

    def step(self,state,command,dt=None,prescribed_d=None):
        c = self.c
        dt = c.dt if dt is None else float(dt)
        a = self.tau/(self.tau+dt)
        Ealg = c.E_inf+np.dot(a,self.Ebranch)
        memory = np.einsum("i,ab,ieb->ea",a*self.Ebranch,self.D,state.z)
        rhs = self.assemble_stress(memory)
        dynamic = c.tool_mass/dt**2+c.actuator_c/dt+c.actuator_k
        tool_rhs = (c.tool_mass/dt**2+c.actuator_c/dt)*state.d+c.tool_mass/dt*state.v+c.actuator_k*command
        if dt not in self._bulk:
            self._bulk[dt] = sparse.block_diag((Ealg*self.Kunit,sparse.csc_matrix([[dynamic]])),format="csc")
        K = self._bulk[dt]
        right = np.r_[rhs,tool_rhs]
        x = np.r_[state.u,state.d]
        free = np.r_[self.free,self.nd] if prescribed_d is None else self.free
        if prescribed_d is not None:
            x[-1] = prescribed_d
        for iteration in range(c.newton_max):
            contact,J,force,gap,points,pressure = self.contact(x[:-1],x[-1])
            residual = K@x-right+contact
            error = float(np.max(np.abs(residual[free])))
            if error < c.newton_tol:
                break
            tangent=(K+J).tocsc()[free,:][:,free]
            delta=spsolve(tangent,-residual[free])
            if not np.all(np.isfinite(delta)):
                raise RuntimeError("Nonfinite contact solve")
            x[free] += delta
        else:
            raise RuntimeError(f"Contact Newton failed: residual={error:.3e}")
        strain = self.strain(x[:-1])
        z = a[:,None,None]*state.z+(1-a[:,None,None])*strain
        new = State(x[:-1],z,float(x[-1]),float((x[-1]-state.d)/dt),state.t+dt)
        sigma = c.E_inf*(strain@self.D.T)+np.einsum("i,ab,ieb->ea",self.Ebranch,self.D,strain[None]-z)
        fint = self.assemble_stress(sigma)
        base_reaction = float(np.sum(fint[self.fixed[1::2]]))
        body_balance = abs(base_reaction-force)
        actuator = c.actuator_k*(command-new.d)-c.actuator_c*new.v
        tool_balance = abs(actuator-force-c.tool_mass*(new.v-state.v)/dt)
        eps_tensor = np.array([strain[:,0],strain[:,1],strain[:,2]/np.sqrt(2)]).T
        max_strain = float(np.max(np.linalg.norm(eps_tensor,axis=1)))
        energy = .5*np.sum(self.area*c.thickness*c.E_inf*np.einsum("ea,ab,eb->e",strain,self.D,strain))
        for i in range(2):
            v = strain-z[i]
            energy += .5*np.sum(self.area*c.thickness*self.Ebranch[i]*np.einsum("ea,ab,eb->e",v,self.D,v))
        diag = np.array([body_balance,tool_balance,max(0,float(gap.max())),max_strain,energy,iteration+1,error])
        return new,force,diag

    def marker_values(self,u):
        return u.reshape(-1,2)[self.marker_nodes,0]*self.marker_sign

    def simulate(self,commands,phases=None,state=None,dt=None,metadata=None,actual_positions=None):
        started=time.perf_counter()
        commands=np.asarray(commands,dtype=float)
        phases=np.array(phases if phases is not None else ["future"]*len(commands))
        state=self.initial() if state is None else state.copy()
        states=[state.copy()]
        first_contact=self.contact(state.u,state.d)
        forces=[first_contact[2]]
        diagnostics=[np.zeros(7)]
        for i,command in enumerate(commands):
            prescribed=None if actual_positions is None else actual_positions[i]
            state,force,diag=self.step(state,command,dt,prescribed)
            states.append(state)
            forces.append(force)
            diagnostics.append(diag)
        return Trace(cast_config(self.c),np.array([s.t for s in states]),
                     np.r_[commands[0] if len(commands) else state.d,commands],
                     np.concatenate((["initial"],phases)),np.array([s.u for s in states]),np.array([s.z for s in states]),
                     np.array([s.d for s in states]),np.array([s.v for s in states]),np.array(forces),
                     np.array([self.marker_values(s.u) for s in states]),np.array(diagnostics),
                     time.perf_counter()-started,metadata or {})


def cast_config(c):
    return c.asdict()
