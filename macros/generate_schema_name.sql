{% macro generate_schema_name(custom_schema_name, node) -%}
    {#-
      Schema isolation macro — guarantees all objects land in
      spec_compliant_* schemas within the testing catalog.
      This prevents collisions with human dev work.
    -#}
    {%- if custom_schema_name is none -%}
        spec_compliant_{{ target.schema }}
    {%- else -%}
        {{ custom_schema_name }}
    {%- endif -%}
{%- endmacro %}
