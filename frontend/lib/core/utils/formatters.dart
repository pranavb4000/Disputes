import 'package:intl/intl.dart';

/// Display formatting for Indian users. The API sends UTC; the UI shows IST.
abstract final class Formatters {
  static const Duration _istOffset = Duration(hours: 5, minutes: 30);

  static final NumberFormat _inr = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 2);
  static final NumberFormat _count = NumberFormat.decimalPattern('en_IN');
  static final DateFormat _dateTime = DateFormat('dd MMM yyyy, hh:mm a');
  static final DateFormat _date = DateFormat('dd MMM yyyy');

  /// ₹1,00,000.00 (Indian digit grouping).
  static String inr(num amount) => _inr.format(amount);

  /// 1,00,000
  static String count(num value) => _count.format(value);

  static DateTime toIst(DateTime value) => value.toUtc().add(_istOffset);

  /// 24 Sep 2026, 06:45 PM IST
  static String dateTimeIst(DateTime? value) => value == null ? '—' : '${_dateTime.format(toIst(value))} IST';

  static String dateIst(DateTime? value) => value == null ? '—' : _date.format(toIst(value));
}
