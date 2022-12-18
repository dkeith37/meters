;(function(){
    const toastIt = document.getElementById('toast')
    const toast = new bootstrap.Toast(toastIt)

    document.body.addEventListener("showToast", function(evt){
        document.getElementById('toastMessage').innerHTML = evt.detail.value
        toast.show()
    })
})();