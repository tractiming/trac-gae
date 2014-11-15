
if (sessionStorage.access_token == null) {
    //link to login page
    location.href="/login.html";
}
else{
    
}

    $(document).ready(function() {
$("a.logout").click(function(){
    sessionStorage.clear();
    location.href="/login.html";
});
    });