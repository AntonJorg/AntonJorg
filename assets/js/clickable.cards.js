$(document).ready(function(){
    $(".card-body").addClass("collapsed");

    $(".card").click(function(){
      var elem = $(this).find(".card-body");

      if (elem.hasClass("expanded")) {
        elem.removeClass("expanded").addClass("collapsed");
      } else {
        elem.removeClass("collapsed").addClass("expanded");
      }
    });
  });