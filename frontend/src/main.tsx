import { React, JSX, ReactDOM } from './recovered/runtime.js';
import { OriginalShell } from './recovered/OriginalShell.js';
ReactDOM.createRoot(document.getElementById('root')!).render(JSX.jsx(React.StrictMode, {children: JSX.jsx(OriginalShell, {})}));
