import torch
from torch import nn
from dynamics import MaxwellRollout,ClosureRollout,constants

MODEL_NAMES=['snapshot_state','history_state','history_single','gru_contact']


class Base(nn.Module):
    def __init__(self,cfg,material):
        super().__init__();self.encoder=nn.GRU(5,cfg['hidden_size'],batch_first=True)
        self.register_buffer('scale',torch.tensor([.006,.02,8.,.006,cfg['dt']]))
        self.register_buffer('constants',torch.tensor(constants(material,cfg),dtype=torch.float64))
    def encode(self,h):return self.encoder(h/self.scale)[1]


class StateModel(Base):
    """Future controller never enters the state encoder. Only initial split learns."""
    def __init__(self,cfg,material,snapshot=False):
        super().__init__(cfg,material);self.snapshot=snapshot;self.head=nn.Linear(cfg['hidden_size'],1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
    def state(self,h):
        hidden=self.encode(h[:,-1:] if self.snapshot else h)[-1]
        fraction=torch.sigmoid(self.head(hidden));k0,k1,k2=self.constants[:3].to(h.dtype)
        stress=torch.clamp((k0+k1+k2)*h[:,-1,0]-h[:,-1,2],min=1e-6)[:,None]
        return torch.cat([fraction*stress/k1,(1-fraction)*stress/k2],-1)
    def forward(self,h,u,controls):
        return MaxwellRollout.apply(self.state(h),h[:,-1,:2],u,controls,self.constants)


class GRUContact(Base):
    """Competitive temporal baseline: known actuator/contact; learned future closure.
    Known K,D condition the decoder and the common actuator solve. No future y.
    It receives more trainable capacity than the structured two-state encoder.
    """
    def __init__(self,cfg,material):
        super().__init__(cfg,material);self.dt=cfg['dt'];self.horizon=cfg['future_seconds']
        self.switch_steps=round(cfg['controller_switch_time']/self.dt)
        self.old_control=[cfg['plant']['stiffness']/2200.,cfg['plant']['damping']/45.]
        self.decoder=nn.GRU(10,cfg['hidden_size'],batch_first=True);self.head=nn.Linear(cfg['hidden_size'],1)
        nn.init.constant_(self.head.bias,-1.)
    def forward(self,h,u,controls):
        B,T=u.shape;hidden=self.encode(h);du=torch.diff(u,dim=1,prepend=h[:,-1,3:4])
        t=torch.arange(1,T+1,device=u.device,dtype=u.dtype)*self.dt/self.horizon
        now=(h[:,-1]/self.scale)[:,None].expand(-1,T,-1)
        ctrl=(controls/controls.new_tensor([2200.,45.]))[:,None].expand(-1,T,-1).clone()
        ctrl[:,:self.switch_steps]=controls.new_tensor(self.old_control)
        inp=torch.cat([u[...,None]/.006,du[...,None]/.001,t[None,:,None].expand(B,-1,-1),now,ctrl],-1)
        q=.010*torch.sigmoid(self.head(self.decoder(inp,hidden)[0]).squeeze(-1))
        return ClosureRollout.apply(q,h[:,-1,:2],u,controls,self.constants)


def make_model(name,cfg,material):
    if name=='gru_contact':return GRUContact(cfg,material)
    if name in MODEL_NAMES:return StateModel(cfg,material,name=='snapshot_state')
    raise ValueError(name)


def loss(pred,label):
    return ((pred[...,2]-label[...,2])/8).square().mean()+((pred[...,0]-label[...,0])/.006).square().mean()

