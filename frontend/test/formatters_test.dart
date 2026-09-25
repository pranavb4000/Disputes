import 'package:dms_web/core/utils/formatters.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('INR uses Indian digit grouping and the rupee sign', () {
    expect(Formatters.inr(100000), '₹1,00,000.00');
    expect(Formatters.inr(12345678.5), '₹1,23,45,678.50');
  });

  test('counts use Indian grouping', () {
    expect(Formatters.count(1234567), '12,34,567');
  });

  test('UTC timestamps are shown in IST', () {
    final utc = DateTime.utc(2026, 9, 24, 13, 15);
    expect(Formatters.dateTimeIst(utc), '24 Sep 2026, 06:45 PM IST');
    expect(Formatters.dateTimeIst(null), '—');
  });
}
