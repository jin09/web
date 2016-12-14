/**
 * Created by gautam on 12-12-2016.
 */
// [START initialize_firebase_in_sw]
// Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/3.5.2/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.5.2/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in the
// messagingSenderId.
 // Initialize Firebase
  var config = {
    apiKey: "AIzaSyAW6A0sHVsM2GDg8aCps3fkvL-6oFkzzsU",
    authDomain: "backend-108.firebaseapp.com",
    databaseURL: "https://backend-108.firebaseio.com",
    storageBucket: "backend-108.appspot.com",
    messagingSenderId: "467653905030"
  };
  firebase.initializeApp(config);

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
// [END initialize_firebase_in_sw]

messaging.setBackgroundMessageHandler(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  // Customize notification here
  const notificationTitle = 'New Incoming Request';
  const notificationOptions = {
    body: 'Please reload the page!!'
  };

  return self.registration.showNotification(notificationTitle,
      notificationOptions);
});