"""
Test Suite 2: Home Page (Landing Page)
Verifies:
- HTTP GET / renders status 200 OK
- Correct template resolution (core/landing.html)
- Hero section: title, subtitle, and primary call-to-action buttons
- Core content sections:
  1. How SKYsense AI works (Image -> AI Preprocessing -> Xception Model -> Rainfall Classification -> Interactive Dashboard)
  2. AI capabilities (Image Analysis, Rainfall Classification, Confidence Estimation, Historical Analysis)
  3. Technology stack (Python, TensorFlow / Keras, Xception, Django, SQLite, JavaScript, Chart.js)
  4. Research & academic context (Academic Research, Evaluation, Future IoT Integration)
  5. Future architecture with explicit Future Work disclaimer for IoT
  6. Master's Degree Project footer
- Navigation state changes for anonymous vs authenticated users
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class HomePageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('core:landing')

    def test_home_page_status_and_template(self):
        """Verifies GET / returns 200 OK and uses core/landing.html."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/landing.html')

    def test_hero_section_branding_and_cta(self):
        """Verifies hero title, subtitle, and primary call-to-action buttons."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SKYsense AI')
        self.assertContains(response, 'AI-Powered Cloud &amp; Rainfall Intelligence')
        self.assertContains(response, 'Analyze cloud imagery using deep learning to estimate rainfall conditions.')
        self.assertContains(response, 'Analyze an Image')
        self.assertContains(response, 'Explore Dashboard')

    def test_how_it_works_section(self):
        """Verifies Section 1: How SKYsense AI works and workflow steps."""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'How SKYsense AI Works')
        self.assertContains(response, 'Image')
        self.assertContains(response, 'AI Preprocessing')
        self.assertContains(response, 'Xception Model')
        self.assertContains(response, 'Rainfall Classification')
        self.assertContains(response, 'Interactive Dashboard')

    def test_ai_capabilities_section(self):
        """Verifies Section 2: AI capabilities."""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'AI Capabilities')
        self.assertContains(response, 'Image Analysis')
        self.assertContains(response, 'Rainfall Classification')
        self.assertContains(response, 'Confidence Estimation')
        self.assertContains(response, 'Historical Analysis')

    def test_technology_section(self):
        """Verifies Section 3: Technology stack mentions."""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Technology Stack')
        self.assertContains(response, 'Python')
        self.assertContains(response, 'TensorFlow / Keras')
        self.assertContains(response, 'Xception')
        self.assertContains(response, 'Django')
        self.assertContains(response, 'SQLite')
        self.assertContains(response, 'JavaScript')
        self.assertContains(response, 'Chart.js')

    def test_research_and_future_architecture_section(self):
        """Verifies Section 4 & 5: Research context and Future IoT Architecture."""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Research &amp; Methodology')
        self.assertContains(response, 'Future Architecture')
        self.assertContains(response, 'Future Work')

    def test_footer_branding_and_project_details(self):
        """Verifies Section 6: Footer contains Master's degree project attribution."""
        response = self.client.get(self.home_url)
        self.assertContains(response, "Master's Degree Project")
        self.assertContains(response, 'AI + Cloud Computing + Future IoT Integration')

    def test_anonymous_user_navigation(self):
        """Verifies anonymous user sees Sign In and Register links."""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Sign In')
        self.assertContains(response, 'Register')
        self.assertNotContains(response, 'title="Sign out"')

    def test_authenticated_user_navigation(self):
        """Verifies logged-in user sees Dashboard, Predict, Profile, and Sign Out links."""
        user = User.objects.create_user(username='landing_tester', password='TestPassword123!')
        self.client.force_login(user)

        response = self.client.get(self.home_url)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Predict')
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'title="Sign out"')
