from .context import stadv, call_assert

import tensorflow as tf
import numpy as np


class FlowLossCase(tf.test.TestCase):
    """Test the flow_loss loss function."""

    def setUp(self):
        # dimensions of the flow "random" shape for generic cases
        self.N, self.H, self.W = 2, 7, 6
        flow_shape = (self.N, 2, self.H, self.W)
        self.flow_zero = np.zeros(flow_shape, dtype=int)

        self.flows = tf.placeholder(tf.float32, shape=None, name='flows')

        self.loss_symmetric = stadv.losses.flow_loss(self.flows, 'SYMMETRIC')
        self.loss_constant = stadv.losses.flow_loss(self.flows, 'CONSTANT')

    def test_zero_flow(self):
        """Make sure that null flows (all 0) gives a flow loss of 0."""
        with self.test_session():
            loss_symmetric = self.loss_symmetric.eval(feed_dict={
                self.flows: self.flow_zero
            })
            loss_constant = self.loss_constant.eval(feed_dict={
                self.flows: self.flow_zero
            })

            call_assert(
                self.assertAllClose,
                loss_symmetric, np.zeros(loss_symmetric.shape),
                msg='0 flow with symmetric padding gives != 0 loss'
            )
            call_assert(
                self.assertAllClose,
                loss_constant, np.zeros(loss_constant.shape),
                msg='0 flow with constant padding gives != 0 loss'
            )

    def test_constant_flow(self):
        """Make sure that a constant flow gives 0 loss for symmetric padding."""
        with self.test_session():
            custom_flow = self.flow_zero + 4.3
            loss_symmetric = self.loss_symmetric.eval(feed_dict={
                self.flows: custom_flow
            })

            call_assert(
                self.assertAllClose,
                np.amax(loss_symmetric), 0.,
                msg='constant flow with symmetric padding gives > 0 loss'
            )

class AdvLossCase(tf.test.TestCase):
    """Test the adv_loss loss function."""

    def setUp(self):
        self.unscaled_logits = tf.placeholder(
            tf.float32, shape=None, name='unscaled_logits'
        )
        self.targets = tf.placeholder(
            tf.int32, shape=[None], name='targets'
        )
        self.kappa = tf.placeholder(tf.float32, shape=[])
        self.loss = stadv.losses.adv_loss(
            self.unscaled_logits, self.targets, self.kappa
        )
        self.loss_default_kappa = stadv.losses.adv_loss(
            self.unscaled_logits, self.targets
        )

    def test_numerical_correctness_with_example(self):
        """Test numerical correctness for a concrete case."""
        unscaled_logits_example = np.array(
            [[-20.3, 4.7, 5.8, 7.2], [77.5, -0.2, 9.2, -12.0]]
        )
        targets_example = np.array([2, 0])

        # first term in loss is expected to be [7.2 9.2]
        # second term in loss is expected to be [5.8 77.5]
        # final loss is expected to be [max(1.4, -kappa) max(-68.3, -kappa)
        # i.e., for kappa=0: [1.4 0], for kappa=10: [1.4 -10]
        expected_result_kappa_0 = np.array([1.4, 0.])
        expected_result_kappa_10 = np.array([1.4, -10.])

        with self.test_session():
            loss_kappa_0 = self.loss.eval(feed_dict={
                self.unscaled_logits: unscaled_logits_example,
                self.targets: targets_example,
                self.kappa: 0.
            })
            val_loss_default_kappa = self.loss_default_kappa.eval(feed_dict={
                self.unscaled_logits: unscaled_logits_example,
                self.targets: targets_example
            })
            loss_kappa_10 = self.loss.eval(feed_dict={
                self.unscaled_logits: unscaled_logits_example,
                self.targets: targets_example,
                self.kappa: 10.
            })

            call_assert(
                self.assertAllClose,
                val_loss_default_kappa, loss_kappa_0,
                msg='default kappa argument differs from setting kappa=0',
            )
            call_assert(
                self.assertAllClose,
                loss_kappa_0, expected_result_kappa_0,
                msg='wrong loss for kappa=0'
            )
            call_assert(
                self.assertAllClose,
                loss_kappa_10, expected_result_kappa_10,
                msg='wrong loss for kappa=10'
            )

if __name__ == '__main__':
    tf.test.main()
