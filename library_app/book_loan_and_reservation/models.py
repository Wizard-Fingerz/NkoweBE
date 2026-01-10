from django.db import models

from account.models import CustomUser
from library_app.models import Book, Member


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="loans")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="loans")
    borrowed_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member}"

class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="reservations")
    reserved_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.book.title} reserved by {self.member}"


class Fine(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="fines")
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    date_issued = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Fine for {self.member} - {self.amount}"
