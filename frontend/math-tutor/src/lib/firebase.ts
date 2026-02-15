import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyB-JHRNw3uIVO8ZWwR034ed4nOZwgLZIm8",
  authDomain: "math11-d6970.firebaseapp.com",
  projectId: "math11-d6970",
  storageBucket: "math11-d6970.firebasestorage.app",
  messagingSenderId: "1055781047927",
  appId: "1:1055781047927:web:57f677ca817105d6db4072",
};

// Prevent multiple app initialization in dev mode
const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
