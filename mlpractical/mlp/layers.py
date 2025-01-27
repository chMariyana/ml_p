# -*- coding: utf-8 -*-
"""Layer definitions.

This module defines classes which encapsulate a single layer.

These layers map input activations to output activation with the `fprop`
method and map gradients with repsect to outputs to gradients with respect to
their inputs with the `bprop` method.

Some layers will have learnable parameters and so will additionally define
methods for getting and setting parameter and calculating gradients with
respect to the layer parameters.
"""

import numpy as np
import mlp.initialisers as init
from mlp import DEFAULT_SEED
from scipy.signal import convolve2d as conv2d 
from scipy.ndimage.interpolation import rotate
#from mlp.im2col import im2col_indices
#from mlp.im2col import col2im_indices

class Layer(object):
    """Abstract class defining the interface for a layer."""

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        raise NotImplementedError()

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        raise NotImplementedError()


class LayerWithParameters(Layer):
    """Abstract class defining the interface for a layer with parameters."""

    def grads_wrt_params(self, inputs, grads_wrt_outputs):
        """Calculates gradients with respect to layer parameters.

        Args:
            inputs: Array of inputs to layer of shape (batch_size, input_dim).
            grads_wrt_to_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            List of arrays of gradients with respect to the layer parameters
            with parameter gradients appearing in same order in tuple as
            returned from `get_params` method.
        """
        raise NotImplementedError()

    def params_penalty(self):
        """Returns the parameter dependent penalty term for this layer.

        If no parameter-dependent penalty terms are set this returns zero.
        """
        raise NotImplementedError()

    @property
    def params(self):
        """Returns a list of parameters of layer.

        Returns:
            List of current parameter values. This list should be in the
            corresponding order to the `values` argument to `set_params`.
        """
        raise NotImplementedError()

    @params.setter
    def params(self, values):
        """Sets layer parameters from a list of values.

        Args:
            values: List of values to set parameters to. This list should be
                in the corresponding order to what is returned by `get_params`.
        """
        raise NotImplementedError()


class StochasticLayerWithParameters(Layer):
    """Specialised layer which uses a stochastic forward propagation."""

    def __init__(self, rng=None):
        """Constructs a new StochasticLayer object.

        Args:
            rng (RandomState): Seeded random number generator object.
        """
        if rng is None:
            rng = np.random.RandomState(DEFAULT_SEED)
        self.rng = rng

    def fprop(self, inputs, stochastic=True):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            stochastic: Flag allowing different deterministic
                forward-propagation mode in addition to default stochastic
                forward-propagation e.g. for use at test time. If False
                a deterministic forward-propagation transformation
                corresponding to the expected output of the stochastic
                forward-propagation is applied.

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        raise NotImplementedError()

    def grads_wrt_params(self, inputs, grads_wrt_outputs):
        """Calculates gradients with respect to layer parameters.

        Args:
            inputs: Array of inputs to layer of shape (batch_size, input_dim).
            grads_wrt_to_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            List of arrays of gradients with respect to the layer parameters
            with parameter gradients appearing in same order in tuple as
            returned from `get_params` method.
        """
        raise NotImplementedError()

    def params_penalty(self):
        """Returns the parameter dependent penalty term for this layer.

        If no parameter-dependent penalty terms are set this returns zero.
        """
        raise NotImplementedError()

    @property
    def params(self):
        """Returns a list of parameters of layer.

        Returns:
            List of current parameter values. This list should be in the
            corresponding order to the `values` argument to `set_params`.
        """
        raise NotImplementedError()

    @params.setter
    def params(self, values):
        """Sets layer parameters from a list of values.

        Args:
            values: List of values to set parameters to. This list should be
                in the corresponding order to what is returned by `get_params`.
        """
        raise NotImplementedError()


class StochasticLayer(Layer):
    """Specialised layer which uses a stochastic forward propagation."""

    def __init__(self, rng=None):
        """Constructs a new StochasticLayer object.

        Args:
            rng (RandomState): Seeded random number generator object.
        """
        if rng is None:
            rng = np.random.RandomState(DEFAULT_SEED)
        self.rng = rng

    def fprop(self, inputs, stochastic=True):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            stochastic: Flag allowing different deterministic
                forward-propagation mode in addition to default stochastic
                forward-propagation e.g. for use at test time. If False
                a deterministic forward-propagation transformation
                corresponding to the expected output of the stochastic
                forward-propagation is applied.

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        raise NotImplementedError()

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs. This should correspond to
        default stochastic forward-propagation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        raise NotImplementedError()


class AffineLayer(LayerWithParameters):
    """Layer implementing an affine tranformation of its inputs.

    This layer is parameterised by a weight matrix and bias vector.
    """

    def __init__(self, input_dim, output_dim,
                 weights_initialiser=init.UniformInit(-0.1, 0.1),
                 biases_initialiser=init.ConstantInit(0.),
                 weights_penalty=None, biases_penalty=None):
        """Initialises a parameterised affine layer.

        Args:
            input_dim (int): Dimension of inputs to the layer.
            output_dim (int): Dimension of the layer outputs.
            weights_initialiser: Initialiser for the weight parameters.
            biases_initialiser: Initialiser for the bias parameters.
            weights_penalty: Weights-dependent penalty term (regulariser) or
                None if no regularisation is to be applied to the weights.
            biases_penalty: Biases-dependent penalty term (regulariser) or
                None if no regularisation is to be applied to the biases.
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.weights = weights_initialiser((self.output_dim, self.input_dim))
        self.biases = biases_initialiser(self.output_dim)
        self.weights_penalty = weights_penalty
        self.biases_penalty = biases_penalty

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        For inputs `x`, outputs `y`, weights `W` and biases `b` the layer
        corresponds to `y = W.dot(x) + b`.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return self.weights.dot(inputs.T).T + self.biases

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return grads_wrt_outputs.dot(self.weights)

    def grads_wrt_params(self, inputs, grads_wrt_outputs):
        """Calculates gradients with respect to layer parameters.

        Args:
            inputs: array of inputs to layer of shape (batch_size, input_dim)
            grads_wrt_to_outputs: array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim)

        Returns:
            list of arrays of gradients with respect to the layer parameters
            `[grads_wrt_weights, grads_wrt_biases]`.
        """

        grads_wrt_weights = np.dot(grads_wrt_outputs.T, inputs)
        grads_wrt_biases = np.sum(grads_wrt_outputs, axis=0)

        if self.weights_penalty is not None:
            grads_wrt_weights += self.weights_penalty.grad(parameter=self.weights)

        if self.biases_penalty is not None:
            grads_wrt_biases += self.biases_penalty.grad(parameter=self.biases)

        return [grads_wrt_weights, grads_wrt_biases]

    def params_penalty(self):
        """Returns the parameter dependent penalty term for this layer.

        If no parameter-dependent penalty terms are set this returns zero.
        """
        params_penalty = 0
        if self.weights_penalty is not None:
            params_penalty += self.weights_penalty(self.weights)
        if self.biases_penalty is not None:
            params_penalty += self.biases_penalty(self.biases)
        return params_penalty

    @property
    def params(self):
        """A list of layer parameter values: `[weights, biases]`."""
        return [self.weights, self.biases]

    @params.setter
    def params(self, values):
        self.weights = values[0]
        self.biases = values[1]

    def __repr__(self):
        return 'AffineLayer(input_dim={0}, output_dim={1})'.format(
            self.input_dim, self.output_dim)


class SigmoidLayer(Layer):
    """Layer implementing an element-wise logistic sigmoid transformation."""

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        For inputs `x` and outputs `y` this corresponds to
        `y = 1 / (1 + exp(-x))`.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return 1. / (1. + np.exp(-inputs))

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return grads_wrt_outputs * outputs * (1. - outputs)

    def __repr__(self):
        return 'SigmoidLayer'

class ConvolutionalLayer(LayerWithParameters):
    """Layer implementing a 2D convolution-based transformation of its inputs.
    The layer is parameterised by a set of 2D convolutional kernels, a four
    dimensional array of shape
        (num_output_channels, num_input_channels, kernel_height, kernel_dim_2)
    and a bias vector, a one dimensional array of shape
        (num_output_channels,)
    i.e. one shared bias per output channel.
    Assuming no-padding is applied to the inputs so that outputs are only
    calculated for positions where the kernel filters fully overlap with the
    inputs, and that unit strides are used the outputs will have spatial extent
        output_height = input_height - kernel_height + 1
        output_width = input_width - kernel_width + 1
    """

    def __init__(self, num_input_channels, num_output_channels,
                 input_height, input_width,
                 kernel_height, kernel_width,
                 kernels_init=init.UniformInit(-0.01, 0.01),
                 biases_init=init.ConstantInit(0.),
                 kernels_penalty=None, biases_penalty=None):
        """Initialises a parameterised convolutional layer.
        Args:
            num_input_channels (int): Number of channels in inputs to
                layer (this may be number of colour channels in the input
                images if used as the first layer in a model, or the
                number of output channels, a.k.a. feature maps, from a
                a previous convolutional layer).
            num_output_channels (int): Number of channels in outputs
                from the layer, a.k.a. number of feature maps.
            input_height (int): Size of first input dimension of each 2D
                channel of inputs.
            input_width (int): Size of second input dimension of each 2D
                channel of inputs.
            kernel_height (int): Size of first dimension of each 2D channel of
                kernels.
            kernel_width (int): Size of second dimension of each 2D channel of
                kernels.
            kernels_intialiser: Initialiser for the kernel parameters.
            biases_initialiser: Initialiser for the bias parameters.
            kernels_penalty: Kernel-dependent penalty term (regulariser) or
                None if no regularisation is to be applied to the kernels.
            biases_penalty: Biases-dependent penalty term (regulariser) or
                None if no regularisation is to be applied to the biases.
        """
        self.num_input_channels = num_input_channels
        self.num_output_channels = num_output_channels
        self.input_height = input_height
        self.input_width = input_width
        self.kernel_height = kernel_height
        self.kernel_width = kernel_width
        self.kernels_init = kernels_init
        self.biases_init = biases_init
        self.kernels_shape = (
            num_output_channels, num_input_channels, kernel_height, kernel_width
        )
        self.inputs_shape = (
            None, num_input_channels, input_height, input_width
        )
        self.kernels = self.kernels_init(self.kernels_shape)
        self.biases = self.biases_init(num_output_channels)
        self.kernels_penalty = kernels_penalty
        self.biases_penalty = biases_penalty

        self.cache = None

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.
        For inputs `x`, outputs `y`, kernels `K` and biases `b` the layer
        corresponds to `y = conv2d(x, K) + b`.
        Args:
            inputs: Array of layer inputs of shape (batch_size, num_input_channels, image_height, image_width).
        Returns:
            outputs: Array of layer outputs of shape (batch_size, num_output_channels, output_height, output_width).
        """
        
        outputs = []
        
        for batch in range(inputs.shape[0]):   
            outputs_temp = []
            for num_output_c in range(self.num_output_channels):
                output = 0.
                
                for num_input_c in range(self.num_input_channels):
                    output += conv2d(inputs[batch][num_input_c], self.kernels[num_output_c][num_input_c], mode = 'valid')
                output += self.biases[num_output_c]
                outputs_temp.append(output)
            outputs.append(outputs_temp)  
        return np.array(outputs)        
        #raise NotImplementedError

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.
        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.
        Args:
            inputs: Array of layer inputs of shape
                (batch_size, num_input_channels, input_height, input_width).
            outputs: Array of layer outputs calculated in forward pass of
                shape
                (batch_size, num_output_channels, output_height, output_width).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape
                (batch_size, num_output_channels, output_height, output_width).
        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, num_input_channels, input_height, input_width).
        """
        #raise NotImplementedError
        outputs = []
        for batch in range(grads_wrt_outputs.shape[0]): 
            outputs_temp = []
            for num_input_c in range(self.num_input_channels):
                output = 0.
                for num_output_c in range(self.num_output_channels):
                    output += conv2d(grads_wrt_outputs[batch][num_output_c], 
                                     rotate(rotate(self.kernels[num_output_c][num_input_c], 90.0), 90),  
                                            mode = 'full')
                outputs_temp.append(output)
            outputs.append(outputs_temp)  
        return np.array(outputs)

    def grads_wrt_params(self, inputs, grads_wrt_outputs):
        """Calculates gradients with respect to layer parameters.
        Args:
            inputs: array of inputs to layer of shape (batch_size, input_dim)
            grads_wrt_to_outputs: array of gradients with respect to the layer
                outputs of shape
                (batch_size, num_output_channels, output_height, output_width).
        Returns:
            list of arrays of gradients with respect to the layer parameters
            `[grads_wrt_kernels, grads_wrt_biases]`.
        """
        
        
        grads_wrt_kernels = np.zeros((self.num_output_channels, self.num_input_channels, self.kernel_height, self.kernel_width))
        grads_wrt_biases = np.zeros(self.num_output_channels)
        for batch in range(grads_wrt_outputs.shape[0]):
            for num_output_channels in range(self.num_output_channels):
                grads_wrt_biases[num_output_channels] += grads_wrt_outputs[batch][num_output_channels].sum()
                for num_input_channels in range(self.num_input_channels):
                    grads_wrt_kernels[num_output_channels, num_input_channels] += conv2d(grads_wrt_outputs[batch,num_output_channels], rotate(rotate(inputs[batch, num_input_channels], 90.0), 90.0), mode = 'valid')
        return [np.array(grads_wrt_kernels), np.array(grads_wrt_biases)]

        
        #raise NotImplementedError

    def params_penalty(self):
        """Returns the parameter dependent penalty term for this layer.
        If no parameter-dependent penalty terms are set this returns zero.
        """
        params_penalty = 0
        if self.kernels_penalty is not None:
            params_penalty += self.kernels_penalty(self.kernels)
        if self.biases_penalty is not None:
            params_penalty += self.biases_penalty(self.biases)
        return params_penalty

    @property
    def params(self):
        """A list of layer parameter values: `[kernels, biases]`."""
        return [self.kernels, self.biases]

    @params.setter
    def params(self, values):
        self.kernels = values[0]
        self.biases = values[1]

    def __repr__(self):
        return (
            'ConvolutionalLayer(\n'
            '    num_input_channels={0}, num_output_channels={1},\n'
            '    input_height={2}, input_width={3},\n'
            '    kernel_height={4}, kernel_width={5}\n'
            ')'
                .format(self.num_input_channels, self.num_output_channels,
                        self.input_height, self.input_width, self.kernel_height,
                        self.kernel_width)
        )

class MaxPooling2DLayer(Layer):
    """
    A class implementing a MaxPooling2D layer.
    """
    def __init__(self, input_height, input_width, size, stride):
        """
        Initializes a max pooling 2D layer
        :param input_height: The image height of the input images
        :param input_width: The image width of the input images
        :param size: The size of the max pooling kernel, indicated as an int
        :param stride: The stride of the max pooling layer, i.e. how many pixels we move the max pooling filter (in the
         relevant axis) at each step during the scanning process
        """
        self.input_height = input_height
        self.input_width = input_width
        self.size = size
        self.stride = stride
        self.cache = None
        self.all_inds= []
        self.X_col = []
        self.max_idx  = []
        
########################################################        
    def get_im2col_indices(self,x_shape, field_height, field_width, padding=1, stride=1):
  # First figure out what the size of the output should be
        N, C, H, W = x_shape
        assert (H + 2 * padding - field_height) % stride == 0
        assert (W + 2 * padding - field_height) % stride == 0
        out_height = int((H + 2 * padding - field_height) / stride + 1)
        out_width = int((W + 2 * padding - field_width) / stride + 1)

        i0 = np.repeat(np.arange(field_height), field_width)
        i0 = np.tile(i0, C)
        i1 = stride * np.repeat(np.arange(out_height), out_width)
        j0 = np.tile(np.arange(field_width), field_height * C)
        j1 = stride * np.tile(np.arange(out_width), out_height)
        i = i0.reshape(-1, 1) + i1.reshape(1, -1)
        j = j0.reshape(-1, 1) + j1.reshape(1, -1)

        k = np.repeat(np.arange(C), field_height * field_width).reshape(-1, 1)

        return (k, i, j)


    def im2col_indices(self,x, field_height, field_width, padding=1, stride=1):
        """ An implementation of im2col based on some fancy indexing """
  # Zero-pad the input
        p = padding
        x_padded = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)), mode='constant')
        st = int(stride)

        k, i, j = self.get_im2col_indices(x.shape, field_height, field_width, padding,
                               st)

        cols = x_padded[:, k, i, j]
        C = x.shape[1]
        cols = cols.transpose(1, 2, 0).reshape(field_height * field_width * C, -1)
        return cols


    def col2im_indices(self,cols, x_shape, field_height=3, field_width=3, padding=1,
                   stride=1):
        """ An implementation of col2im based on fancy indexing and np.add.at """
        N, C, H, W = x_shape
        H_padded, W_padded = H + 2 * padding, W + 2 * padding
        x_padded = np.zeros((N, C, H_padded, W_padded), dtype=cols.dtype)
        k, i, j = self.get_im2col_indices(x_shape, field_height, field_width, padding,
                               stride)
        cols_reshaped = cols.reshape(C * field_height * field_width, -1, N)
        cols_reshaped = cols_reshaped.transpose(2, 0, 1)
        np.add.at(x_padded, (slice(None), k, i, j), cols_reshaped)
        if padding == 0:
            return x_padded
        return x_padded[:, :, padding:-padding, padding:-padding]
        
        
        
###############################################################        
        
        
        
    def fprop(self, inputs):
        """
        Given an input of shape (b, c, input_height, input_width), apply the max pooling function without padding.
        :param inputs: Inputs of size (b, c, input_height, input_width)
        :return: The output of the max pooling operation. Assuming a stride=2 the output should have a shape of
        (b, c, (input_height - size)/stride + 1, (input_width - size)/stride + 1)
        """
        h_out = int((self.input_height - self.size)/self.stride + 1)
        w_out = int((self.input_width - self.size)/self.stride + 1)

        n = inputs.shape[0]
        d = inputs.shape[1]
        h = self.input_height 
        w = self.input_width 
        X_reshaped = inputs.reshape(n * d, 1, h, w)

        strd = int(self.stride)
        sz = int(self.size)
        X_col = self.im2col_indices(X_reshaped, sz, sz, padding= 0, stride=strd)
        self.X_col = X_col

        max_idx = np.argmax(X_col, axis=0)
        self.max_idx = max_idx


        out = X_col[max_idx, range(max_idx.size)]

        out = out.reshape(h_out, w_out, n, d)


        out = out.transpose(2, 3, 0, 1)

            #print(self.all_inds)
        return out

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """
        Given the inputs, outputs and grads_wrt_outputs of the max pooling layer, compute the grads_wrt_inputs
        :param inputs:  Inputs of size (b, c, input_height, input_width)
        :param outputs: The output of the max pooling layer fprop function. Assuming a stride=2 the output should have a shape of
        (b, c, (input_height - size)/stride + 1, (input_width - size)/stride + 1)
        :param grads_wrt_outputs: The grads wrt to the outputs, of shape equal to that of the outputs.
        :return: grads_wrt_input, of shape equal to the inputs.
        """
        
        #raise NotImplementedError
        xs = int((self.input_height - self.size)/self.stride + 1)
        ys = int((self.input_width - self.size)/self.stride + 1)
        n = inputs.shape[0]
        d = inputs.shape[1]
        h = self.input_height 
        w = self.input_width 

        dX_col = np.zeros_like(self.X_col)

        dout_flat = grads_wrt_outputs.transpose(2, 3, 0, 1).ravel()


        dX_col[self.max_idx, range(self.max_idx.size)] = dout_flat

        dX = self.col2im_indices(dX_col, (n * d, 1, h, w), self.size, self.size, padding=0, stride=self.stride)

        dX = dX.reshape(inputs.shape)

        return np.array(dX)


class ReluLayer(Layer):
    """Layer implementing an element-wise rectified linear transformation."""

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        For inputs `x` and outputs `y` this corresponds to `y = max(0, x)`.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return np.maximum(inputs, 0.)

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return (outputs > 0) * grads_wrt_outputs

    def __repr__(self):
        return 'ReluLayer'


class TanhLayer(Layer):
    """Layer implementing an element-wise hyperbolic tangent transformation."""

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        For inputs `x` and outputs `y` this corresponds to `y = tanh(x)`.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return np.tanh(inputs)

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return (1. - outputs ** 2) * grads_wrt_outputs

    def __repr__(self):
        return 'TanhLayer'


class SoftmaxLayer(Layer):
    """Layer implementing a softmax transformation."""

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        For inputs `x` and outputs `y` this corresponds to

            `y = exp(x) / sum(exp(x))`.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        # subtract max inside exponential to improve numerical stability -
        # when we divide through by sum this term cancels
        exp_inputs = np.exp(inputs - inputs.max(-1)[:, None])
        return exp_inputs / exp_inputs.sum(-1)[:, None]

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return (outputs * (grads_wrt_outputs -
                           (grads_wrt_outputs * outputs).sum(-1)[:, None]))

    def __repr__(self):
        return 'SoftmaxLayer'


class RadialBasisFunctionLayer(Layer):
    """Layer implementing projection to a grid of radial basis functions."""

    def __init__(self, grid_dim, intervals=[[0., 1.]]):
        """Creates a radial basis function layer object.

        Args:
            grid_dim: Integer specifying how many basis function to use in
                grid across input space per dimension (so total number of
                basis functions will be grid_dim**input_dim)
            intervals: List of intervals (two element lists or tuples)
                specifying extents of axis-aligned region in input-space to
                tile basis functions in grid across. For example for a 2D input
                space spanning [0, 1] x [0, 1] use intervals=[[0, 1], [0, 1]].
        """
        num_basis = grid_dim ** len(intervals)
        self.centres = np.array(np.meshgrid(*[
            np.linspace(low, high, grid_dim) for (low, high) in intervals])
                                ).reshape((len(intervals), -1))
        self.scales = np.array([
            [(high - low) * 1. / grid_dim] for (low, high) in intervals])

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return np.exp(-(inputs[..., None] - self.centres[None, ...]) ** 2 /
                      self.scales ** 2).reshape((inputs.shape[0], -1))

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        num_basis = self.centres.shape[1]
        return -2 * (
                ((inputs[..., None] - self.centres[None, ...]) / self.scales ** 2) *
                grads_wrt_outputs.reshape((inputs.shape[0], -1, num_basis))
        ).sum(-1)

    def __repr__(self):
        return 'RadialBasisFunctionLayer(grid_dim={0})'.format(self.grid_dim)


class DropoutLayer(StochasticLayer):
    """Layer which stochastically drops input dimensions in its output."""

    def __init__(self, rng=None, incl_prob=0.5, share_across_batch=True):
        """Construct a new dropout layer.

        Args:
            rng (RandomState): Seeded random number generator.
            incl_prob: Scalar value in (0, 1] specifying the probability of
                each input dimension being included in the output.
            share_across_batch: Whether to use same dropout mask across
                all inputs in a batch or use per input masks.
        """
        super(DropoutLayer, self).__init__(rng)
        assert incl_prob > 0. and incl_prob <= 1.
        self.incl_prob = incl_prob
        self.share_across_batch = share_across_batch
        self.rng = rng

    def fprop(self, inputs, stochastic=True):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            stochastic: Flag allowing different deterministic
                forward-propagation mode in addition to default stochastic
                forward-propagation e.g. for use at test time. If False
                a deterministic forward-propagation transformation
                corresponding to the expected output of the stochastic
                forward-propagation is applied.

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        if stochastic:
            mask_shape = (1,) + inputs.shape[1:] if self.share_across_batch else inputs.shape
            self._mask = (self.rng.uniform(size=mask_shape) < self.incl_prob)
            return inputs * self._mask
        else:
            return inputs * self.incl_prob

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs. This should correspond to
        default stochastic forward-propagation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return grads_wrt_outputs * self._mask

    def __repr__(self):
        return 'DropoutLayer(incl_prob={0:.1f})'.format(self.incl_prob)


class ReshapeLayer(Layer):
    """Layer which reshapes dimensions of inputs."""

    def __init__(self, output_shape=None):
        """Create a new reshape layer object.

        Args:
            output_shape: Tuple specifying shape each input in batch should
                be reshaped to in outputs. This **excludes** the batch size
                so the shape of the final output array will be
                    (batch_size, ) + output_shape
                Similarly to numpy.reshape, one shape dimension can be -1. In
                this case, the value is inferred from the size of the input
                array and remaining dimensions. The shape specified must be
                compatible with the input array shape - i.e. the total number
                of values in the array cannot be changed. If set to `None` the
                output shape will be set to
                    (batch_size, -1)
                which will flatten all the inputs to vectors.
        """
        self.output_shape = (-1,) if output_shape is None else output_shape

    def fprop(self, inputs):
        """Forward propagates activations through the layer transformation.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).

        Returns:
            outputs: Array of layer outputs of shape (batch_size, output_dim).
        """
        return inputs.reshape((inputs.shape[0],) + self.output_shape)

    def bprop(self, inputs, outputs, grads_wrt_outputs):
        """Back propagates gradients through a layer.

        Given gradients with respect to the outputs of the layer calculates the
        gradients with respect to the layer inputs.

        Args:
            inputs: Array of layer inputs of shape (batch_size, input_dim).
            outputs: Array of layer outputs calculated in forward pass of
                shape (batch_size, output_dim).
            grads_wrt_outputs: Array of gradients with respect to the layer
                outputs of shape (batch_size, output_dim).

        Returns:
            Array of gradients with respect to the layer inputs of shape
            (batch_size, input_dim).
        """
        return grads_wrt_outputs.reshape(inputs.shape)

    def __repr__(self):
        return 'ReshapeLayer(output_shape={0})'.format(self.output_shape)

    
    

    