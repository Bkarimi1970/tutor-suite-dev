function App() {
  const handleClick = () => {
    window.grecaptcha.enterprise.ready(() => {
      window.grecaptcha.enterprise
        .execute("6LdLyWAsAAAAAJRxZ3bF33oRWhDpN8-KVhvcauf5", { action: "test" })
        .then((token) => {
          console.log("Enterprise token:", token);
          alert("reCAPTCHA Enterprise executed ✅");
        });
    });
  };

  return (
    <div style={{ padding: "40px" }}>
      <h2>reCAPTCHA Enterprise Test</h2>
      <button onClick={handleClick}>Click once</button>
    </div>
  );
}

export default App;
