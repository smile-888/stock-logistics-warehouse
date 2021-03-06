# Copyright (C) 2011 Julius Network Solutions SARL <contact@julius.fr>
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_common import TestsCommon
from odoo.exceptions import ValidationError


class TestMoveLocation(TestsCommon):

    def setUp(self):
        super().setUp()
        self.setup_product_amounts()

    def _create_wizard(self, origin_location, destination_location):
        return self.wizard_obj.create({
            "origin_location_id": origin_location.id,
            "destination_location_id": destination_location.id,
        })

    def test_move_location_wizard(self):
        """Test a simple move."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        wizard.add_lines()
        wizard.action_move_location()
        self.check_product_amount(
            self.product_no_lots, self.internal_loc_1, 0,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_1, 0, self.lot1,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_1, 0, self.lot2,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_1, 0, self.lot3,
        )
        self.check_product_amount(
            self.product_no_lots, self.internal_loc_2, 123,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_2, 1, self.lot1,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_2, 1, self.lot2,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_2, 1, self.lot3,
        )

    def test_move_location_wizard_amount(self):
        """Can't move more than exists."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        wizard.add_lines()
        with self.assertRaises(ValidationError):
            wizard.stock_move_location_line_ids[0].move_quantity += 1

    def test_move_location_wizard_ignore_reserved(self):
        """Can't move more than exists."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        wizard.add_lines()
        # reserve some quants
        self.quant_obj._update_reserved_quantity(
            self.product_no_lots,
            self.internal_loc_1,
            50,
        )
        self.quant_obj._update_reserved_quantity(
            self.product_lots,
            self.internal_loc_1,
            1,
            lot_id=self.lot1,
        )
        # doesn't care about reservations, everything is moved
        wizard.action_move_location()
        self.check_product_amount(
            self.product_no_lots, self.internal_loc_1, 0,
        )
        self.check_product_amount(
            self.product_no_lots, self.internal_loc_2, 123,
        )
        self.check_product_amount(
            self.product_lots, self.internal_loc_2, 1, self.lot1,
        )

    def test_wizard_clear_lines(self):
        """Test lines getting cleared properly."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        wizard.add_lines()
        self.assertEqual(len(wizard.stock_move_location_line_ids), 4)
        wizard._onchange_locations()
        self.assertEqual(len(wizard.stock_move_location_line_ids), 0)

    def test_planned_transfer(self):
        """Test planned transfer."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        wizard.add_lines()
        wizard.with_context({'planned': True}).action_move_location()
        picking = wizard.picking_id
        self.assertEqual(picking.state, 'draft')
        self.assertEqual(len(picking.move_line_ids), 4)
        self.assertEqual(
            sorted(picking.move_line_ids.mapped("qty_done")),
            [1, 1, 1, 123],
        )
