if (sessionStorage.access_token == null) {
    //link to login page
    location.href="/login.html";
}
else{
    
}

$("#logout").click(function(){
    sessionStorage.clear();
    location.href="/login.html";
});