import numbersContent from '../../../content/first20/lessons11-20.json';
import { NumbersAnimatedDemo } from '../components/NumbersAnimatedDemo';
import foundationContent from '../../../content/first20/lessons4-10.json';
import { adaptLessons } from './adaptLessons.js';
import { FoundationsDemo } from '../components/FoundationsDemo';
export const additionalLessons = adaptLessons([...foundationContent,...numbersContent]);
export function AdditionalVisual(props) { return JSX.jsx(Number(props.visual?.order)>=11?NumbersAnimatedDemo:FoundationsDemo,props); }
import { JSX } from './runtime.js';
import { EnhancedFeatureVisual, EnhancedMethodVisual } from './mainVisualAdapters.js';
import { OriginalHelpDemo } from '../components/OriginalHelpDemo';
import { algorithmHelpEntry, originalHelpExample } from './originalHelp.js';
export const algorithmHelp = originalHelpExample(algorithmHelpEntry);
export function OriginalFeatureVisual(props) { return JSX.jsx(props.visual?.isOriginalHelp ? OriginalHelpDemo : EnhancedFeatureVisual, props); }
export function OriginalMethodVisual(props) { return JSX.jsx(props.visual?.isOriginalHelp ? OriginalHelpDemo : EnhancedMethodVisual, props); }
export function AlgorithmHelpVisual(props) { return JSX.jsx(OriginalHelpDemo, props); }
