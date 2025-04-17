// Firebase authentication logic
document.addEventListener('DOMContentLoaded', function() {
    // Check if Firebase config is available
    if (typeof firebaseConfig === 'undefined') {
        console.error('Firebase configuration not found!');
        disableFirebaseButtons();
        return;
    }

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    
    // Initialize Firebase Auth
    const auth = firebase.auth();
    const provider = new firebase.auth.GoogleAuthProvider();
    
    // Listen for auth state changes
    auth.onAuthStateChanged(function(user) {
        if (user) {
            console.log('User is signed in:', user);
            // User is signed in, hide login button and show logout button
            hideLoginButtons();
            showUserInfo(user);
        } else {
            console.log('No user is signed in.');
            // User is signed out, show login button and hide logout button
            showLoginButtons();
            hideUserInfo();
        }
    });
    
    // Add click event to all Google sign-in buttons
    const googleButtons = document.querySelectorAll('.google-signin-btn');
    googleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            signInWithGoogle();
        });
    });
    
    // Add click event to logout buttons
    const logoutButtons = document.querySelectorAll('.google-signout-btn');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            signOut();
        });
    });
    
    // Sign in with Google
    function signInWithGoogle() {
        auth.signInWithPopup(provider)
            .then(function(result) {
                // This gives you a Google Access Token
                const token = result.credential.accessToken;
                // The signed-in user info
                const user = result.user;
                console.log('Google sign in success:', user);
                
                // Send the ID token to your backend
                user.getIdToken().then(function(idToken) {
                    // Send the token to your server
                    authenticateWithBackend(idToken, user);
                });
            })
            .catch(function(error) {
                console.error('Google sign in error:', error);
                // Handle errors here
                const errorCode = error.code;
                const errorMessage = error.message;
                // The email of the user's account used
                const email = error.email;
                // The firebase.auth.AuthCredential type that was used
                const credential = error.credential;
                
                alert('Errore di accesso: ' + errorMessage);
            });
    }
    
    // Sign out
    function signOut() {
        auth.signOut()
            .then(function() {
                console.log('User signed out');
                // Redirect to home or login page
                window.location.href = '/logout';
            })
            .catch(function(error) {
                console.error('Sign out error:', error);
            });
    }
    
    // Send authentication token to backend
    function authenticateWithBackend(idToken, user) {
        fetch('/firebase-auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                idToken: idToken,
                email: user.email,
                displayName: user.displayName,
                photoURL: user.photoURL
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            if (data.success) {
                // Redirect to dashboard or intended page
                window.location.href = data.redirect || '/dashboard';
            } else {
                alert('Errore di autenticazione: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Errore di comunicazione con il server');
        });
    }
    
    // Helper functions for UI
    function showLoginButtons() {
        document.querySelectorAll('.auth-loggedout').forEach(el => {
            el.style.display = 'block';
        });
        document.querySelectorAll('.auth-loggedin').forEach(el => {
            el.style.display = 'none';
        });
    }
    
    function hideLoginButtons() {
        document.querySelectorAll('.auth-loggedout').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.auth-loggedin').forEach(el => {
            el.style.display = 'block';
        });
    }
    
    function showUserInfo(user) {
        const userInfoElements = document.querySelectorAll('.user-info');
        userInfoElements.forEach(el => {
            el.innerHTML = `
                <div class="d-flex align-items-center">
                    <img src="${user.photoURL}" alt="${user.displayName}" class="rounded-circle me-2" width="32" height="32">
                    <span>${user.displayName}</span>
                </div>
            `;
        });
    }
    
    function hideUserInfo() {
        const userInfoElements = document.querySelectorAll('.user-info');
        userInfoElements.forEach(el => {
            el.innerHTML = '';
        });
    }
    
    function disableFirebaseButtons() {
        const buttons = document.querySelectorAll('.google-signin-btn, .google-signout-btn');
        buttons.forEach(button => {
            button.disabled = true;
            button.innerHTML = 'Firebase non configurato';
            button.classList.add('disabled');
        });
    }
});