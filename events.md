---
layout: page
title: Events
permalink: /events/
---

{% assign event_posts = site.posts | where_exp: "post", "post.categories contains 'events'" %}
{% assign future_events = event_posts | where_exp: "post", "post.date >= site.time" %}
{% assign past_events = event_posts | where_exp: "post", "post.date < site.time" %}

## Upcoming Events
{% if future_posts.size > 0 %}
{% for post in future_posts %}
- {{ post.date | date: "%b %d, %Y" }} - [{{ post.title }}]({{ post.url }})
{% endfor %}
{% else %}
No upcoming events scheduled.
{% endif %}

## Past Events
{% if past_posts.size > 0 %}
{% for post in past_posts limit: 5 %}
- {{ post.date | date: "%b %d, %Y" }} - [{{ post.title }}]({{ post.url }})
{% endfor %}
{% else %}
No past events.
{% endif %}
