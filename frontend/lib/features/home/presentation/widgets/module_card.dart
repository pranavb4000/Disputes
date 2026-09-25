import 'package:flutter/material.dart';

import '../../../../core/theme/brand_colors.dart';
import '../../data/models/home_models.dart';

/// Card for one product module (UPI, IMPS, ...). Inactive modules are shown greyed out.
class ModuleCard extends StatelessWidget {
  const ModuleCard({super.key, required this.module, this.onOpen});

  final ModuleCardData module;
  final VoidCallback? onOpen;

  @override
  Widget build(BuildContext context) {
    final available = module.isEnabled && module.hasAccess;
    final status = !module.isEnabled
        ? 'Coming soon'
        : module.hasAccess
            ? module.roles.join(' · ')
            : 'No access';

    return Container(
      width: 240,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: BrandColors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: available ? BrandColors.maroon : BrandColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.account_balance_outlined,
                color: available ? BrandColors.maroon : BrandColors.disabled,
              ),
              const SizedBox(width: 8),
              Text(
                module.name,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: available ? BrandColors.textPrimary : BrandColors.disabled,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            module.description ?? '',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: available ? BrandColors.textPrimary : BrandColors.disabled, fontSize: 13),
          ),
          const SizedBox(height: 12),
          Text(status, style: const TextStyle(color: BrandColors.textPrimary, fontSize: 12)),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: available ? onOpen : null,
            child: const Text('Open'),
          ),
        ],
      ),
    );
  }
}
