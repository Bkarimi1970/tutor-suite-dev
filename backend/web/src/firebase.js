import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { getFirestore, doc, getDoc, setDoc } from "firebase/firestore";

const firebaseConfig = {apiKey: "AIzaSyB-JHRNw3uIVO8ZWwR034ed4nOZwgLZIm8",

  authDomain: "math11-d6970.firebaseapp.com",

  projectId: "math11-d6970",

  storageBucket: "math11-d6970.firebasestorage.app",

  messagingSenderId: "1055781047927",

  appId: "1:1055781047927:web:57f677ca817105d6db4072",

  measurementId: "G-0GRDRC7DR6"

};

const app = initializeApp(firebaseConfig);

// ===== Auth =====
export const auth = getAuth(app);

const provider = new GoogleAuthProvider();

export async function loginWithGoogle() {
  const result = await signInWithPopup(auth, provider);
  return result.user;
}

// ===== Firestore =====
export const db = getFirestore(app);

export async function getUserProfile(uid) {
  if (!uid) throw new Error("Missing uid");
  const ref = doc(db, "users", uid);
  const snap = await getDoc(ref);
  return snap.exists() ? snap.data() : null;
}

export async function saveUserProfile(uid, { name, curriculum, country }) {
  if (!uid) throw new Error("Missing uid");
  const ref = doc(db, "users", uid);
  await setDoc(
    ref,
    { name, curriculum, country },
    { merge: true }
  );
}
