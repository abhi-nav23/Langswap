import { useState } from "react";
import CodeEditor from "./components/Editor";
import axios from "axios";
import "./App.css";

function App() {
  const [inputCode, setInputCode] = useState(`a = int(input("Enter a number: "))\nb = 5\nprint("Sum is", a + b)`);
  const [outputCode, setOutputCode] = useState("// Translated C++ code will appear here");
  const [loading, setLoading] = useState(false); // ✅ Add loading state

  const handleTranslate = async () => {
    try {
      setLoading(true); // ✅ Show loading
      const response = await axios.post("http://localhost:8000/translate", {
        code: inputCode,
      });
      setOutputCode(response.data.cpp || "// Translation failed.");
    } catch (err) {
      setOutputCode("// ❌ Error connecting to backend.");
    } finally {
      setLoading(false); // ✅ Always stop loading
    }
  };

  return (
    <>
      <div className="header">LangSwap 🔁 Python to C++ Translator</div>

      <div className="container">
        <div className="editor-container">
          <div className="editor-block">
            <h3>Python Code</h3>
            <CodeEditor language="python" value={inputCode} onChange={setInputCode} />
          </div>

          <div className="editor-block">
            <h3>C++ Output</h3>
            <CodeEditor language="cpp" value={outputCode} onChange={() => {}} />
          </div>
        </div>

        <button className="translate-btn" onClick={handleTranslate} disabled={loading}>
          {loading ? "Translating..." : "🔁 Translate"}
        </button>
      </div>
    </>
  );
}

export default App;
