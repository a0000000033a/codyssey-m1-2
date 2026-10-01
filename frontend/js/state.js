export function createState(){
  return {stock:null,conversationId:null,generation:0,busy:false,pending:null,
    ticket(){return this.generation;},isCurrent(ticket){return this.generation===ticket;},
    selectStock(stock){this.generation++;this.stock=stock;this.conversationId=null;this.pending=null;this.busy=false;},
    reset(){this.selectStock(null);}};
}
