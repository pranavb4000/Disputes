import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import 'models/home_models.dart';

class HomeRepository {
  HomeRepository(this._dio);

  final Dio _dio;

  Future<HomeSummary> fetchHome() => _get('/home', HomeSummary.fromJson);

  Future<ModuleSummary> fetchModuleSummary(String moduleCode) =>
      _get('/${moduleCode.toLowerCase()}/summary', ModuleSummary.fromJson);

  Future<T> _get<T>(String path, T Function(Map<String, dynamic>) parse) async {
    try {
      final response = await _dio.get<dynamic>(path);
      return unwrapEnvelope(response, (data) => parse(data! as Map<String, dynamic>));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}

final homeRepositoryProvider = Provider<HomeRepository>((ref) => HomeRepository(ref.watch(apiDioProvider)));
