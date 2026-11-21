import {scenarios} from './content.ts';
export type SessionEvent={scenario:number;state:'reviewed'|'approved'|'denied'|'suggested'};
export function canRecord(events:SessionEvent[],scenario:number,state:SessionEvent['state']):boolean{
 const prior=events.filter(e=>e.scenario===scenario);
 if(state==='reviewed')return !prior.length;
 if(!prior.length)return false;
 if(state==='suggested')return !!scenarios[scenario].assistance&&!prior.some(e=>e.state==='suggested');
 return scenarios[scenario].verdict==='HOLD'&&!prior.some(e=>e.state==='approved'||e.state==='denied');
}
export function validateRequest(values:{name:string;email:string;message:string}):Record<string,'required'|'invalidEmail'>{
 const errors:Record<string,'required'|'invalidEmail'>={};
 for(const key of ['name','email','message'] as const)if(!values[key].trim())errors[key]='required';
 if(values.email.trim()&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim()))errors.email='invalidEmail';
 return errors;
}
