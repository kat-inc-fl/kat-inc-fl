---
layout: default
title: Resources
---

# Resources

*Last updated: {{ site.data.resources.last_updated | date: "%B %d, %Y at %I:%M %p UTC" }}*

## Table of Contents

{% for heading_data in site.data.resources.headings %}
  {% assign heading_name = heading_data[0] %}
  {% assign heading_slug = heading_name | slugify %}
- [{{ heading_name }}](#{{ heading_slug }})
{% endfor %}

---

{% for heading_data in site.data.resources.headings %}
  {% assign heading_name = heading_data[0] %}
  {% assign heading_content = heading_data[1] %}
  {% assign heading_slug = heading_name | slugify %}
  
# {{ heading_name }} {#{{ heading_slug }}}

  {% comment %}Handle direct links (no sub-headings){% endcomment %}
  {% if heading_content.direct_links %}
    {% for entry in heading_content.direct_links %}
- {% if entry.url %}[{{ entry.name }}]({{ entry.url }}){% else %}{{ entry.name }}{% endif %}
    {% endfor %}
  {% endif %}
  
  {% comment %}Handle sub-headings{% endcomment %}
  {% if heading_content.sub_headings %}
    {% for subheading_data in heading_content.sub_headings %}
      {% assign subheading_name = subheading_data[0] %}
      {% assign entries = subheading_data[1] %}
      
## {{ subheading_name }}

      {% for entry in entries %}
- {% if entry.url %}[{{ entry.name }}]({{ entry.url }}){% else %}{{ entry.name }}{% endif %}
      {% endfor %}
      
    {% endfor %}
  {% endif %}
  
{% endfor %}

---

*This page is automatically generated from our [Google Sheets database](https://docs.google.com/spreadsheets/d/11OpF8wS5vUyeX4gAJZrMpB57RQ1vgmwygudmsffDQVQ/edit?usp=sharing). To suggest updates or additions, please modify the spreadsheet or [contact us](mailto:your-email@example.com).*
