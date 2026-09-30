import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, [this.statusCode]);
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? httpClient, FlutterSecureStorage? storage})
    : _http = httpClient ?? http.Client(),
      _storage = storage ?? const FlutterSecureStorage();

  static const defaultBaseUrl = String.fromEnvironment(
    'DEXORA_API_URL',
    defaultValue: 'http://10.0.2.2:8002/api/v1',
  );
  static const _tokenKey = 'dexora_api_token';
  static const _serverKey = 'dexora_api_url';
  final http.Client _http;
  final FlutterSecureStorage _storage;
  String? _token;
  String _baseUrl = defaultBaseUrl;

  bool get isAuthenticated => _token?.isNotEmpty == true;
  String get baseUrl => _baseUrl;

  Future<bool> restoreSession() async {
    _baseUrl = await _storage.read(key: _serverKey) ?? defaultBaseUrl;
    _token = await _storage.read(key: _tokenKey);
    return isAuthenticated;
  }

  Future<void> configureServer(String value) async {
    final normalized = value.trim().replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !uri.hasAuthority ||
        !{'http', 'https'}.contains(uri.scheme)) {
      throw const ApiException('Escribe una dirección de servidor válida.');
    }
    _baseUrl = normalized;
    await _storage.write(key: _serverKey, value: normalized);
  }

  Future<void> login(String username, String password) async {
    final data = await post(
      '/auth/login/',
      body: {'username': username, 'password': password},
      authenticated: false,
    );
    _token = data['token'] as String?;
    if (_token == null) {
      throw const ApiException('La respuesta no contiene un token válido.');
    }
    await _storage.write(key: _tokenKey, value: _token);
  }

  Future<void> logout() async {
    try {
      if (isAuthenticated) await post('/auth/logout/');
    } finally {
      _token = null;
      await _storage.delete(key: _tokenKey);
    }
  }

  Future<dynamic> get(
    String path, {
    Map<String, String?> query = const {},
  }) async {
    return _decode(await _http.get(_uri(path, query), headers: _headers()));
  }

  Future<dynamic> post(
    String path, {
    Map<String, dynamic>? body,
    bool authenticated = true,
  }) async {
    return _decode(
      await _http.post(
        _uri(path),
        headers: _headers(authenticated),
        body: jsonEncode(body ?? {}),
      ),
    );
  }

  Future<dynamic> patch(
    String path, {
    required Map<String, dynamic> body,
  }) async {
    return _decode(
      await _http.patch(
        _uri(path),
        headers: _headers(),
        body: jsonEncode(body),
      ),
    );
  }

  Future<void> delete(String path) async {
    _decode(await _http.delete(_uri(path), headers: _headers()));
  }

  Uri _uri(String path, [Map<String, String?> query = const {}]) {
    final clean = <String, String>{};
    for (final entry in query.entries) {
      if (entry.value?.isNotEmpty == true) clean[entry.key] = entry.value!;
    }
    return Uri.parse(
      '$_baseUrl$path',
    ).replace(queryParameters: clean.isEmpty ? null : clean);
  }

  Map<String, String> _headers([bool authenticated = true]) => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    if (authenticated && _token != null) 'Authorization': 'Token $_token',
  };

  dynamic _decode(http.Response response) {
    final dynamic data = response.body.isEmpty
        ? null
        : jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = data is Map ? data['detail'] : null;
      throw ApiException(
        detail?.toString() ?? 'No fue posible completar la solicitud.',
        response.statusCode,
      );
    }
    return data;
  }
}
