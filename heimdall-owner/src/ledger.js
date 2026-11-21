// Approval events replace current state, retaining the original action payload.
export function currentItems(events) {
 const items = new Map();
 for(const row of events){const key=row.event.result.key;const old=items.get(key);items.set(key,{...row,payload:row.event.payload||old?.payload});}
 return [...items.values()].reverse();
}
export function canDecide(result,verified,connected){return connected&&verified&&result.tier==='HOLD'&&result.status==='pending';}
export function filterItems(items,query,tier){return items.filter(row=>(tier==='ALL'||row.event.result.tier===tier)&&JSON.stringify(row).toLowerCase().includes(query.toLowerCase()));}
