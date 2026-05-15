# Point 15 Computer Use Core

Goal: Eve uses structured interfaces before visual fallback.

Implemented core:

- `computer/computer_use_observation.py`
- `AppIdentity`
- `UIElement`
- `StructuredInterfaceTree`
- `ComputerUseObservation`
- `ActionPlan`
- `ActionVerification`
- `computer/interface_tree_provider.py`
- providers: BrowserDOMProvider, BrowserAccessibilityProvider, WindowsUIAProvider, VisualFallbackProvider
- `computer/app_permission_model.py`
- `computer/action_router.py` exposes fallback order

Priority order: DOM, accessibility, Windows UIA, app adapter, shortcut, screenshot, OCR, coordinates.

8.6 criterion: core met. Codex 2 must implement/validate live providers.
