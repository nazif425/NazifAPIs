from django.db import models

from salesman.orders.models import (
    BaseOrder,
    BaseOrderItem,
    BaseOrderNote,
    BaseOrderPayment,
)
from salesman.basket.models import BaseBasket, BaseBasketItem


class Order(BaseOrder):
  pass

class OrderItem(BaseOrderItem):
  pass

class OrderPayment(BaseOrderPayment):
  pass

class OrderNote(BaseOrderNote):
  pass


class Basket(BaseBasket):
  pass

class BasketItem(BaseBasketItem):
  pass
  
#from salesman.core.utils import get_salesman_model

#BasketItem = get_salesman_model('BasketItem')
# Create your models here.
