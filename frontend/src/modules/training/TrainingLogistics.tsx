import { FormEvent, useEffect, useState } from 'react';
import { Batch, getBatches, getLogisticsPlans, getAccommodationAllocations, getEligibleTrainees, saveLogisticsPlan, saveAccommodationAllocation, LogisticsPlan, AccommodationAllocation, EligibleTrainee } from './api';

type User={id:number;full_name:string;email:string;role:string;institution_id?:number};

export function TrainingLogistics({user}:{user:User}) {
  const canManage=['NCCT_ADMIN','INSTITUTE_ADMIN','TRAINER'].includes(user.role);
  const [batches,setBatches]=useState<Batch[]>([]);
  const [eligibleTrainees,setEligibleTrainees]=useState<EligibleTrainee[]>([]);
  const [plans,setPlans]=useState<LogisticsPlan[]>([]);
  const [allocations,setAllocations]=useState<AccommodationAllocation[]>([]);
  const [batchId,setBatchId]=useState(0);
  const [message,setMessage]=useState('');
  const [form,setForm]=useState({batch_id:0,hostel_required:false,hostel_name:'',rooms_available:0,meals_included:false,meal_notes:'',transport_required:false,pickup_point:'',transport_notes:'',coordinator_name:'',coordinator_phone:'',notes:''});
  const [allocation,setAllocation]=useState({batch_id:0,trainee_id:0,room_number:'',bed_number:'',status:'ALLOCATED',notes:''});

  async function load(){
    const [b,p]=await Promise.all([getBatches(),getLogisticsPlans()]);
    setBatches(b);setPlans(p);
    const id=batchId||b[0]?.id||0;
    if(id && !batchId){setBatchId(id);setForm(f=>({...f,batch_id:id}));setAllocation(f=>({...f,batch_id:id}));return;}
    if(id){
      const a=await getAccommodationAllocations(id);
      setAllocations(a);
      try {
        const e=await getEligibleTrainees(id);
        setEligibleTrainees(e);
      } catch (e:any) {
        setEligibleTrainees([]);
        setMessage(e.response?.data?.detail||'Could not load eligible trainees. Restart the backend after updating the ERP-09 build.');
      }
    } else {
      setAllocations([]);setEligibleTrainees([]);
    }
  }
  useEffect(()=>{load().catch(e=>setMessage(e.response?.data?.detail||'Could not load training logistics'));},[batchId]);

  const selectedPlan=plans.find(p=>p.batch_id===batchId);
  const already=new Set(allocations.filter(a=>a.batch_id===batchId).map(a=>a.trainee_id));

  async function savePlan(e:FormEvent){e.preventDefault();try{await saveLogisticsPlan({...form,batch_id:Number(form.batch_id),rooms_available:Number(form.rooms_available)});setMessage('Training logistics plan saved.');await load();}catch(e:any){setMessage(e.response?.data?.detail||'Could not save logistics plan');}}
  async function saveAllocation(e:FormEvent){e.preventDefault();try{await saveAccommodationAllocation({...allocation,batch_id:Number(allocation.batch_id),trainee_id:Number(allocation.trainee_id)});setMessage('Hostel allocation saved.');setAllocation(x=>({...x,trainee_id:0,room_number:'',bed_number:'',notes:''}));await load();}catch(e:any){setMessage(e.response?.data?.detail||'Could not save accommodation allocation');}}

  return <div className="training-logistics">
    <section className="panel">
      <div className="panel-title"><div><p className="eyebrow">TRAINING ERP • ERP-09</p><h2>Training Logistics & Hostel</h2><p className="muted">Coordinate accommodation, meals and transport for residential training batches.</p></div><span>{plans.length} plans</span></div>
      {message&&<div className="notice">{message}</div>}
      <div className="form-row" style={{marginTop:12}}><label>Batch<select value={batchId} onChange={e=>{const id=Number(e.target.value);setBatchId(id);setForm(f=>({...f,batch_id:id}));setAllocation(f=>({...f,batch_id:id}))}}>{batches.map(b=><option key={b.id} value={b.id}>{b.batch_code}</option>)}</select></label></div>
    </section>

    {canManage&&<section className="panel">
      <div className="panel-title"><div><h3>Batch logistics plan</h3><p className="muted">Set the services available for this batch.</p></div></div>
      <form className="career-form" onSubmit={savePlan}>
        <div className="form-row"><label><input type="checkbox" checked={form.hostel_required} onChange={e=>setForm({...form,hostel_required:e.target.checked})}/> Hostel required</label><label>Hostel name<input value={form.hostel_name} onChange={e=>setForm({...form,hostel_name:e.target.value})} placeholder="NCCT Training Hostel"/></label></div>
        <div className="form-row"><label>Rooms available<input type="number" min="0" value={form.rooms_available} onChange={e=>setForm({...form,rooms_available:Number(e.target.value)})}/></label><label><input type="checkbox" checked={form.meals_included} onChange={e=>setForm({...form,meals_included:e.target.checked})}/> Meals included</label></div>
        <div className="form-row"><label>Meal notes<input value={form.meal_notes} onChange={e=>setForm({...form,meal_notes:e.target.value})} placeholder="Breakfast + lunch + dinner"/></label><label><input type="checkbox" checked={form.transport_required} onChange={e=>setForm({...form,transport_required:e.target.checked})}/> Transport required</label></div>
        <div className="form-row"><label>Pickup point<input value={form.pickup_point} onChange={e=>setForm({...form,pickup_point:e.target.value})} placeholder="VAMNICOM gate"/></label><label>Transport notes<input value={form.transport_notes} onChange={e=>setForm({...form,transport_notes:e.target.value})}/></label></div>
        <div className="form-row"><label>Coordinator<input value={form.coordinator_name} onChange={e=>setForm({...form,coordinator_name:e.target.value})}/></label><label>Phone<input value={form.coordinator_phone} onChange={e=>setForm({...form,coordinator_phone:e.target.value})}/></label></div>
        <label>Notes<textarea rows={2} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
        <button className="primary">Save logistics plan</button>
      </form>
      {selectedPlan&&<div className="dashboard-attendance-grid" style={{marginTop:12}}>
        <div><span>Hostel</span><strong>{selectedPlan.hostel_required?'Required':'Not required'}</strong><small>{selectedPlan.hostel_name||'—'}</small></div>
        <div><span>Room capacity</span><strong>{selectedPlan.rooms_available}</strong><small>{selectedPlan.allocated_count} allocated</small></div>
        <div><span>Meals</span><strong>{selectedPlan.meals_included?'Included':'Not included'}</strong><small>{selectedPlan.meal_notes||'—'}</small></div>
        <div><span>Transport</span><strong>{selectedPlan.transport_required?'Required':'Not required'}</strong><small>{selectedPlan.pickup_point||'—'}</small></div>
      </div>}
    </section>}

    {canManage&&selectedPlan?.hostel_required&&<section className="panel">
      <div className="panel-title"><div><h3>Hostel allocation</h3><p className="muted">Allocate active trainees in this batch to rooms and beds.</p></div><span>{allocations.filter(a=>a.batch_id===batchId).length} allocated</span></div>
      <form className="career-form" onSubmit={saveAllocation}>
        <div className="form-row"><label>Trainee<select value={allocation.trainee_id} onChange={e=>setAllocation({...allocation,trainee_id:Number(e.target.value)})} required><option value={0}>Select trainee</option>{eligibleTrainees.map(t=><option key={t.trainee_id} value={t.trainee_id}>{t.full_name} • {t.email}{already.has(t.trainee_id)?' (allocated)':''}</option>)}</select></label><label>Room number<input value={allocation.room_number} onChange={e=>setAllocation({...allocation,room_number:e.target.value})} required placeholder="101"/></label></div>
        <div className="form-row"><label>Bed number<input value={allocation.bed_number} onChange={e=>setAllocation({...allocation,bed_number:e.target.value})} placeholder="A"/></label><label>Status<select value={allocation.status} onChange={e=>setAllocation({...allocation,status:e.target.value})}><option>ALLOCATED</option><option>CHECKED_IN</option><option>CHECKED_OUT</option><option>CANCELLED</option></select></label></div>
        <label>Notes<textarea rows={2} value={allocation.notes} onChange={e=>setAllocation({...allocation,notes:e.target.value})}/></label>
        <button className="primary" disabled={!allocation.trainee_id}>Save accommodation</button>
      </form>
      <div className="application-list" style={{marginTop:12}}>{allocations.filter(a=>a.batch_id===batchId).map(a=><div className="application-row" key={a.id}><div><strong>{a.trainee_name}</strong><span>{a.trainee_email}</span><small>Room {a.room_number}{a.bed_number?` • Bed ${a.bed_number}`:''}</small></div><span className="status-badge">{a.status}</span></div>)}{!allocations.filter(a=>a.batch_id===batchId).length&&<div className="empty">No accommodation allocations yet.</div>}</div>
    </section>}

    {!canManage&&<section className="panel"><div className="panel-title"><div><h3>My training logistics</h3><p className="muted">Accommodation and travel information for your active batch.</p></div></div>{plans.map(p=><div className="dashboard-area" key={p.id}><strong>{p.batch_code} • {p.programme_title}</strong><span>{p.hostel_required?`Hostel: ${p.hostel_name||'Provided'} • ${p.allocated_count} allocations`: 'Hostel not required'}{p.meals_included?` • Meals: ${p.meal_notes||'Included'}`:''}{p.transport_required?` • Pickup: ${p.pickup_point||'See coordinator'}`:''}</span></div>)}{!plans.length&&<div className="empty">No logistics information is available for your active training.</div>}</section>}
  </div>;
}
