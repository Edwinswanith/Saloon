import os
import unittest
from unittest.mock import patch

from bson import DBRef, ObjectId

os.environ.setdefault('JWT_SECRET', 'profit-loss-test-secret')

from routes import report_routes


class FakeDocument:
    def __init__(self, **values):
        self._data = dict(values)
        for key, value in values.items():
            setattr(self, key, value)


class FakeQuerySet(list):
    def no_dereference(self):
        return self

    def only(self, *fields):
        return self


class ProfitLossOptimizationTests(unittest.TestCase):
    def test_raw_reference_id_does_not_dereference_dbref(self):
        reference_id = ObjectId()
        document = FakeDocument(product=DBRef('products', reference_id))

        self.assertEqual(
            report_routes._raw_reference_id(document, 'product'),
            reference_id,
        )

    def test_snapshot_product_cost_does_not_need_reference_lookup(self):
        item = FakeDocument(cost_price=42.5, product=DBRef('products', ObjectId()))

        self.assertEqual(report_routes._safe_product_cost(item, {}), 42.5)

    def test_legacy_product_costs_are_loaded_in_one_batch(self):
        legacy_product_id = ObjectId()
        snapshotted_product_id = ObjectId()
        legacy_item = FakeDocument(
            item_type='product',
            cost_price=None,
            product=DBRef('products', legacy_product_id),
        )
        snapshotted_item = FakeDocument(
            item_type='product',
            cost_price=10,
            product=DBRef('products', snapshotted_product_id),
        )
        bill = FakeDocument(items=[legacy_item, snapshotted_item])
        captured_ids = []

        class FakeProduct:
            @staticmethod
            def objects(**query):
                captured_ids.extend(query['id__in'])
                return FakeQuerySet([
                    FakeDocument(id=legacy_product_id, cost=27.25),
                ])

        with patch.object(report_routes, 'Product', FakeProduct):
            costs = report_routes._load_product_costs([bill])

        self.assertEqual(captured_ids, [legacy_product_id])
        self.assertEqual(costs, {str(legacy_product_id): 27.25})
        self.assertEqual(report_routes._safe_product_cost(legacy_item, costs), 27.25)

    def test_legacy_service_names_are_loaded_in_one_batch(self):
        legacy_service_id = ObjectId()
        named_service_id = ObjectId()
        legacy_item = FakeDocument(
            item_type='service',
            name='',
            service=DBRef('services', legacy_service_id),
        )
        named_item = FakeDocument(
            item_type='service',
            name='Stored service name',
            service=DBRef('services', named_service_id),
        )
        bill = FakeDocument(items=[legacy_item, named_item])
        captured_ids = []

        class FakeService:
            @staticmethod
            def objects(**query):
                captured_ids.extend(query['id__in'])
                return FakeQuerySet([
                    FakeDocument(id=legacy_service_id, name='Legacy service'),
                ])

        with patch.object(report_routes, 'Service', FakeService):
            names = report_routes._load_service_names([bill])

        self.assertEqual(captured_ids, [legacy_service_id])
        self.assertEqual(names, {str(legacy_service_id): 'Legacy service'})


if __name__ == '__main__':
    unittest.main()
