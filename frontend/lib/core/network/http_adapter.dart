// Picks the browser adapter on web and a no-op everywhere else (mobile/desktop/tests).
export 'http_adapter_stub.dart' if (dart.library.js_interop) 'http_adapter_web.dart';
