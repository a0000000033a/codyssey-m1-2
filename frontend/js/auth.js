export async function createAuth(config,onChange){
  if(!config.apiKey||!config.authDomain||!config.projectId)throw new Error('Firebase 로그인 설정이 필요합니다. 설정 안내를 확인해주세요.');
  const sdk='https://www.gstatic.com/firebasejs/12.0.0/';
  const [appSDK,authSDK]=await Promise.all([import(sdk+'firebase-app.js'),import(sdk+'firebase-auth.js')]);
  const app=appSDK.initializeApp(config);const auth=authSDK.getAuth(app);
  await authSDK.setPersistence(auth,authSDK.browserSessionPersistence);
  authSDK.onAuthStateChanged(auth,onChange);
  return {login(email,password){return authSDK.signInWithEmailAndPassword(auth,email,password);},
    logout(){return authSDK.signOut(auth);},
    getIdToken(force=false){if(!auth.currentUser)throw new Error('로그인이 필요합니다.');return auth.currentUser.getIdToken(force);}};
}
