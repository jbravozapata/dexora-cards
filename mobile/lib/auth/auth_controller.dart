import 'package:flutter/foundation.dart';

import '../core/api_client.dart';

class AuthController extends ChangeNotifier {
  AuthController(this.api);
  final ApiClient api;
  bool initialized = false;
  bool busy = false;
  bool authenticated = false;
  String? error;

  Future<void> initialize() async {
    authenticated = await api.restoreSession();
    initialized = true;
    notifyListeners();
  }

  Future<bool> login(String username, String password, String server) async {
    busy = true;
    error = null;
    notifyListeners();
    try {
      await api.configureServer(server);
      await api.login(username.trim(), password);
      authenticated = true;
      return true;
    } on ApiException catch (exception) {
      error = exception.message;
      return false;
    } catch (_) {
      error =
          'No se pudo conectar con Dexora. Revisa la dirección del servidor.';
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await api.logout();
    authenticated = false;
    notifyListeners();
  }
}
