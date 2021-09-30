var form = document.querySelector('form')
  var password = document.querySelector('#password1')
  var password2 = document.querySelector('#password2')
  var error = document.querySelector('.password-no-match')
  form.addEventListener('submit', function (event) { 
    if (password.value != password2.value){
        error.hidden = false
        event.preventDefault()
    }
    else {
      error.hidden = true
    }  })