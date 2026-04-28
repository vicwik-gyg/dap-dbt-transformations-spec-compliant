-- Validates dim_suppliers_history: no overlapping validity windows.

select
    a.supplier_id,
    a.valid_from as a_from, a.valid_to as a_to,
    b.valid_from as b_from, b.valid_to as b_to
from {{ ref('dim_suppliers_history') }} as a
inner join {{ ref('dim_suppliers_history') }} as b
    on a.supplier_id = b.supplier_id
    and a.supplier_version_id != b.supplier_version_id
    and a.valid_from < b.valid_to
    and a.valid_to > b.valid_from
