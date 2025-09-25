---
layout: default
title: Resources
---

# Resources

*Last updated: <span id="last-updated-time" data-utc-time="{{ site.data.resources.last_updated }}">{{ site.data.resources.last_updated | date: "%B %d, %Y at %I:%M %p UTC" }}</span>*

<script>
(function() {
    const timeElement = document.getElementById('last-updated-time');
    if (timeElement) {
        const utcTimeString = timeElement.getAttribute('data-utc-time');
        if (utcTimeString) {
            try {
                const utcDate = new Date(utcTimeString);
                const localTimeString = utcDate.toLocaleString(undefined, {
                    year: 'numeric',
                    month: 'long', 
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    timeZoneName: 'short'
                });
                timeElement.textContent = localTimeString;
            } catch (error) {
                console.warn('Could not parse timestamp:', utcTimeString);
                // Fallback: keep the original UTC time display
            }
        }
    }
})();
</script>

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
  
## {{ heading_name }} {#{{ heading_slug }}}

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
      
### {{ subheading_name }}

      {% for entry in entries %}
- {% if entry.url %}[{{ entry.name }}]({{ entry.url }}){% else %}{{ entry.name }}{% endif %}
      {% endfor %}
      
    {% endfor %}
  {% endif %}
  
{% endfor %}

---

*To suggest updates or additions, please [contact us]({% link contact.md %}).*
