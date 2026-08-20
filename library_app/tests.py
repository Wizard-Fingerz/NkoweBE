"""
Regression tests for the Week 1-2 security stabilization pass on library_app.

These exercise the fixes made to library_app/views.py and
library_app/book_loan_and_reservation/views.py:
  - every ViewSet in this app now requires authentication. Previously none
    of them declared permission_classes, so they inherited DRF's own
    built-in default (AllowAny); the project now sets
    DEFAULT_PERMISSION_CLASSES = [IsAuthenticated] globally (see
    nkowebe/settings.py) and each ViewSet also declares it explicitly so
    the access rule doesn't silently change if the global default ever
    does;
  - MemberViewSet.get_queryset scopes non-staff users to their own Member
    record — it used to return every member's personal contact details
    (address, phone_number) to any authenticated user;
  - LibraryCollectionViewSet.get_queryset had its authenticated/anonymous
    branches backwards (unauthenticated requests fell through to
    `LibraryCollection.objects.all()`, i.e. every user's private
    collections). It now returns the requester's own collections plus
    everyone else's PUBLIC ones, with perform_create forcing owner to the
    requesting user rather than trusting client input;
  - LoanViewSet/ReservationViewSet/FineViewSet all scope non-staff users to
    records belonging to their own Member profile via `member__user`.

Written but not yet run from this environment (no reachable Django/Python
execution environment — see the project's migration/CI notes). Please run
`python manage.py test library_app` locally and report back any failures.
"""
from datetime import date, timedelta

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from account.models import CustomUser
from library_app.models import Author, Book, LibraryCollection, Member, Publisher
from library_app.book_loan_and_reservation.models import Fine, Loan, Reservation


def make_user(username, *, is_staff=False, **extra):
    return CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='not-a-real-password-123',
        is_staff=is_staff,
        **extra,
    )


def make_book(isbn, **extra):
    defaults = {'title': f'Book {isbn}', 'isbn': isbn}
    defaults.update(extra)
    return Book.objects.create(**defaults)


class OpenLibraryEndpointsRequireAuthTests(APITestCase):
    """
    AuthorViewSet/PublisherViewSet/BookViewSet/RecentlyAddedBookViewSet
    previously declared no permission_classes at all; anonymous requests
    must now be rejected rather than served.
    """

    def test_authors_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:author-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_publishers_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:publisher-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_books_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:book-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_recently_added_books_endpoint_rejects_anonymous_requests(self):
        response = self.client.get(reverse('api:recentlyaddedbook-list'))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class MemberViewSetScopingTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_lib')
        self.bob = make_user('bob_lib')
        self.staff = make_user('staff_lib', is_staff=True)
        self.alice_member = Member.objects.create(user=self.alice, address='1 Alice St', phone_number='555-0001')
        self.bob_member = Member.objects.create(user=self.bob, address='1 Bob St', phone_number='555-0002')
        self.url = reverse('api:member-list')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_non_staff_user_sees_only_their_own_member_record(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual([row['id'] for row in results], [self.alice_member.pk])

    def test_staff_user_sees_every_member_record(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data['results']}
        self.assertEqual(returned_ids, {self.alice_member.pk, self.bob_member.pk})


class LibraryCollectionViewSetVisibilityTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_col')
        self.bob = make_user('bob_col')
        self.alice_private = LibraryCollection.objects.create(
            name='Alice Private', owner=self.alice, visibility=LibraryCollection.PRIVATE
        )
        self.alice_public = LibraryCollection.objects.create(
            name='Alice Public', owner=self.alice, visibility=LibraryCollection.PUBLIC
        )
        self.bob_private = LibraryCollection.objects.create(
            name='Bob Private', owner=self.bob, visibility=LibraryCollection.PRIVATE
        )
        self.bob_public = LibraryCollection.objects.create(
            name='Bob Public', owner=self.bob, visibility=LibraryCollection.PUBLIC
        )
        self.url = reverse('api:librarycollection-list')

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_user_sees_own_collections_and_others_public_collections_only(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data['results']}
        self.assertEqual(
            returned_ids,
            {self.alice_private.pk, self.alice_public.pk, self.bob_public.pk},
        )
        self.assertNotIn(self.bob_private.pk, returned_ids)

    def test_create_forces_owner_to_requesting_user(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(self.url, {'name': 'New Collection', 'description': ''})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = LibraryCollection.objects.get(name='New Collection')
        self.assertEqual(created.owner_id, self.alice.pk)


class LoanReservationFineScopingTests(APITestCase):
    def setUp(self):
        self.alice = make_user('alice_loan')
        self.bob = make_user('bob_loan')
        self.staff = make_user('staff_loan', is_staff=True)
        self.alice_member = Member.objects.create(user=self.alice)
        self.bob_member = Member.objects.create(user=self.bob)
        self.book = make_book('1111111111111')

        self.alice_loan = Loan.objects.create(
            book=self.book, member=self.alice_member, due_date=date.today() + timedelta(days=14)
        )
        self.bob_loan = Loan.objects.create(
            book=self.book, member=self.bob_member, due_date=date.today() + timedelta(days=14)
        )
        self.alice_reservation = Reservation.objects.create(book=self.book, member=self.alice_member)
        self.bob_reservation = Reservation.objects.create(book=self.book, member=self.bob_member)
        self.alice_fine = Fine.objects.create(member=self.alice_member, amount='5.00', reason='Late return')
        self.bob_fine = Fine.objects.create(member=self.bob_member, amount='7.50', reason='Damaged item')

    def test_loans_are_scoped_to_own_member_record(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:loan-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_loan.pk])

    def test_reservations_are_scoped_to_own_member_record(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:reservation-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_reservation.pk])

    def test_fines_are_scoped_to_own_member_record(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(reverse('api:fine-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in response.data], [self.alice_fine.pk])

    def test_staff_sees_every_loan(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(reverse('api:loan-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row['id'] for row in response.data}
        self.assertEqual(returned_ids, {self.alice_loan.pk, self.bob_loan.pk})
