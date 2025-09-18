---
layout: page
title: Contact
permalink: /contact/
---
# Contact Us

We’d love to hear from you! Please fill out the form below:

<form action="https://formspree.io/f/mnnbeqjb" method="POST" class="contact-form">
  <label for="name">Name</label>
  <input type="text" id="name" name="name" placeholder="Your name" required>

  <label for="email">Email</label>
  <input type="email" id="email" name="_replyto" placeholder="you@example.com" required>

  <label for="message">Message</label>
  <textarea id="message" name="message" rows="6" placeholder="Your message..." required></textarea>

  <input type="submit" value="Send Message">
</form>

## Follow Us

{% raw %}
<div class="social-icons">
  <a href="https://www.facebook.com/koreanadopteestogether" target="_blank" aria-label="Facebook">
    <i class="fab fa-facebook-square fa-2x"></i>
  </a>
  <a href="https://www.instagram.com/koreanadopteestogether/" target="_blank" aria-label="Instagram">
    <i class="fab fa-instagram fa-2x"></i>
  </a>
</div>
{% endraw %}

<style>
/* Modern card-style form */
.contact-form {
  max-width: 600px;
  margin: 2em auto;
  padding: 2em;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  font-family: 'Helvetica Neue', Arial, sans-serif;
  transition: transform 0.2s ease;
}
.contact-form:hover {
  transform: translateY(-3px);
}

.contact-form label {
  font-weight: 600;
  display: block;
  margin-bottom: 0.5em;
  color: #333;
  margin-top: 1em;
}

.contact-form input[type="text"],
.contact-form input[type="email"],
.contact-form textarea {
  width: 100%;
  padding: 0.85em;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.2s;
}

.contact-form input[type="text"]:focus,
.contact-form input[type="email"]:focus,
.contact-form textarea:focus {
  outline: none;
  border-color: #0073e6;
  box-shadow: 0 0 5px rgba(0, 115, 230, 0.3);
}

.contact-form input[type="submit"] {
  width: 100%;
  padding: 0.95em;
  margin-top: 1.5em;
  background: linear-gradient(135deg, #0073e6, #00bfff);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease, transform 0.2s ease;
}

.contact-form input[type="submit"]:hover {
  background: linear-gradient(135deg, #005bb5, #0099e6);
  transform: translateY(-2px);
}

/* Social icons */
.social-icons {
  display: flex;
  gap: 1em;
  margin-top: 2em;
  justify-content: center;
}
.social-icons a {
  color: #333;
  transition: color 0.3s, transform 0.2s;
}
.social-icons a:hover {
  color: #0073e6;
  transform: scale(1.2);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .contact-form {
    padding: 1.5em;
  }
}
</style>
