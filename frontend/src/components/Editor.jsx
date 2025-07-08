import Editor from "@monaco-editor/react";

const CodeEditor = ({ language, value, onChange }) => {
  return (
    <Editor
      height="300px"
      theme="vs-dark"
      language={language}
      value={value}
      onChange={onChange}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
      }}
    />
  );
};

export default CodeEditor;
