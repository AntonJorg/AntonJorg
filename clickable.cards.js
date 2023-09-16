
var coll = document.getElementsByClassName("card");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.querySelector('.card-body');
    if (content !== null) {
      var arrow = this.querySelector('.card-expand');
      if (content.style.maxHeight){
        content.style.maxHeight = null;
        content.style.marginTop = '0px';
        arrow.style.visibility = 'visible';
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
        content.style.marginTop = '15px';
        arrow.style.visibility = 'hidden';
      }    
    }
  });
}
