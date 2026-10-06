export const $=id=>document.getElementById(id);
export function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
export function button(text,onClick,className='button subtle'){const node=el('button',className,text);node.type='button';node.addEventListener('click',onClick);return node;}
export const number=value=>value===null||value===undefined?'—':new Intl.NumberFormat('ko-KR',{maximumFractionDigits:2}).format(value);
export const dateTime=value=>value?new Intl.DateTimeFormat('ko-KR',{dateStyle:'short',timeStyle:'short',timeZone:'Asia/Seoul'}).format(new Date(value)):'—';
