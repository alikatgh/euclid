import numbersContent from '../../../content/first20/lessons11-20.json';
import { NumbersAnimatedDemo } from '../components/NumbersAnimatedDemo';
import foundationContent from '../../../content/first20/lessons4-10.json';
import { adaptLessons } from './adaptLessons.js';
import { FoundationsDemo } from '../components/FoundationsDemo';
const fullBookModules = import.meta.glob('../../../content/fullbook/batch-*.json', { eager: true, import: 'default' });
export const fullBookLessons = Object.values(fullBookModules).flatMap(value => Array.isArray(value) ? value : value.lessons || []);
export const additionalLessons = adaptLessons([...foundationContent,...numbersContent,...fullBookLessons]);
export function AdditionalVisual(props) { const order=Number(props.visual?.order); return JSX.jsx(order>=21?FullBookScene:order>=11?NumbersAnimatedDemo:FoundationsDemo,props); }
import { FullBookScene } from '../components/FullBookScene';
import { JSX } from './runtime.js';
import { EnhancedFeatureVisual, EnhancedMethodVisual } from './mainVisualAdapters.js';
import { OriginalHelpDemo } from '../components/OriginalHelpDemo';
import { algorithmHelpEntry, originalHelpExample } from './originalHelp.js';
export const algorithmHelp = originalHelpExample(algorithmHelpEntry);
export function OriginalFeatureVisual(props) { return JSX.jsx(props.visual?.isOriginalHelp ? OriginalHelpDemo : EnhancedFeatureVisual, props); }
export function OriginalMethodVisual(props) { return JSX.jsx(props.visual?.isOriginalHelp ? OriginalHelpDemo : EnhancedMethodVisual, props); }
export function AlgorithmHelpVisual(props) { return JSX.jsx(OriginalHelpDemo, props); }
