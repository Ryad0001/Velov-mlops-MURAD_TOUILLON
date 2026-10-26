{# Schémas silver / gold tels quels (par défaut dbt les préfixerait : main_silver, main_gold). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name or target.schema }}
{%- endmacro %}
