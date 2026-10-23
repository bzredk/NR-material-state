import torch
from torch import nn
from differentiable import MaxwellRollout,ClosureRollout


class Base(nn.Module):
    def __init__(self,cfg,material):
        super().__init__();h=cfg['hidden_size'];p=cfg['plant'];dt=cfg['dt']
        self.encoder=nn.GRU(5,h,batch_first=True)
        self.register_buffer('scale',torch.tensor([.006,.02,8.,.006,dt]))
        self.register_buffer('constants',torch.tensor([material['k_inf'],*material['k'],*material['tau'],
                                        p['mass'],p['stiffness'],p['damping'],dt],dtype=torch.float64))

    def encode(self,history):
        return self.encoder(history/self.scale)[1]


class StateModel(Base):
    """Current stress fixes one combination; history predicts the hidden split.
    Both snapshot/history use the identical positive state parameterization.
    """
    def __init__(self,cfg,material,snapshot=False):
        super().__init__(cfg,material);self.snapshot=snapshot
        self.head=nn.Linear(cfg['hidden_size'],1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def state(self,history):
        h=self.encode(history[:,-1:] if self.snapshot else history)[-1]
        fraction=torch.sigmoid(self.head(h))
        k0,k1,k2=self.constants[:3].to(history.dtype)
        stress=torch.clamp((k0+k1+k2)*history[:,-1,0]-history[:,-1,2],min=1e-6)[:,None]
        return torch.cat([fraction*stress/k1,(1-fraction)*stress/k2],-1)

    def forward(self,history,commands):
        return MaxwellRollout.apply(self.state(history),history[:,-1,:2],commands,self.constants)


class GRUClosure(Base):
    """Same sequence architecture with/without explicit unilateral contact.
    Future GRU inputs are commands, time, and current observations only.
    It never sees future actual motion or true future contact flags.
    """
    def __init__(self,cfg,material,contact=True):
        super().__init__(cfg,material);self.contact=contact;self.dt=cfg['dt']
        self.decoder=nn.GRU(8,cfg['hidden_size'],batch_first=True)
        self.head=nn.Linear(cfg['hidden_size'],1)
        nn.init.constant_(self.head.bias,-1. if contact else -2.)

    def forward(self,history,commands):
        h=self.encode(history);B,T=commands.shape
        du=torch.diff(commands,dim=1,prepend=history[:,-1,3:4])
        time=torch.arange(1,T+1,device=commands.device,dtype=commands.dtype)*self.dt/4.2
        now=(history[:,-1]/self.scale)[:,None,:].expand(-1,T,-1)
        inp=torch.cat([commands[:,:,None]/.006,du[:,:,None]/.001,
                       time[None,:,None].expand(B,-1,-1),now],-1)
        decoded=self.decoder(inp,h)[0];raw=self.head(decoded).squeeze(-1)
        closure=.010*torch.sigmoid(raw) if self.contact else 8.*torch.nn.functional.softplus(raw)
        return ClosureRollout.apply(closure,history[:,-1,:2],commands,self.constants,self.contact)


def make_model(name,cfg,material):
    if name=='history_state':return StateModel(cfg,material)
    if name=='snapshot_state':return StateModel(cfg,material,snapshot=True)
    if name=='gru_contact':return GRUClosure(cfg,material,True)
    if name=='gru_force':return GRUClosure(cfg,material,False)
    raise ValueError(name)


MODEL_NAMES=['snapshot_state','history_state','gru_contact','gru_force']


def loss(pred,label):
    return ((pred[...,2]-label[...,2])/8.).square().mean()+((pred[...,0]-label[...,0])/.006).square().mean()
