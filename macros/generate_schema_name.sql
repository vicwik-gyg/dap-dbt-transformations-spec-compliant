{% macro generate_schema_name(custom_schema_name, node) -%}
    {#-
      Schema routing macro — all objects land in the target schema (dbt_default)
      because the service principal lacks CREATE SCHEMA on testing catalog.
      Isolation is achieved via model naming (spec_compliant_ prefix in aliases).
    -#}
    {{ target.schema }}
{%- endmacro %}
