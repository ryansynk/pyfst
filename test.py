from math import ceil
import time
from collections import namedtuple
import numpy as np

import torch
import torch.autograd as autograd
import torch.nn.functional as F

import pdb

# dtype = torch.FloatTensor
dtype = torch.cuda.FloatTensor  # Uncomment this to run on GPU

winO = namedtuple('winO', ['nfilt', 'filters', 'filter_params'])

def gabor_window_factory_3D(Ms):
    M1, M2, M3 = Ms[0], Ms[1], Ms[2]

    x1 = np.tile(np.reshape(np.array(range(1, M1 + 1)), [M1, 1, 1]), [1, M2, M3])
    x2 = np.tile(np.reshape(np.array(range(1, M2 + 1)), [1, M2, 1]), [M1, 1, M3])
    x3 = np.tile(np.reshape(np.array(range(1, M3 + 1)), [1, 1, M3]), [M1, M2, 1])

    nfilt = int(np.prod(np.ceil((Ms - 1) / 2.) + 1))

    # out_channels x in_channels x kT x kH x kW
    filters = np.zeros((nfilt, 1, M1, M2, M3), 'complex128')
    filter_params = np.zeros((nfilt, 3))

    winOp = 0
    for m1 in range(0, 1 + int(ceil((Ms[0] - 1) / 2.))):
        for m2 in range(0, 1 + int(ceil((Ms[1] - 1) / 2.))):
            for m3 in range(0, 1 + int(ceil((Ms[2] - 1) / 2.))):
                filters[winOp, 0, :, :, :] = np.exp(2 * np.pi * 1j * (m1 / float(M1) * x1 + \
                    m2 / float(M2) * x2 + m3 / float(M3) * x3)) / np.linalg.norm(Ms);
                filter_params[winOp, :] = [m1, m2, m3];
                winOp = winOp + 1;
    return winO(nfilt, filters, filter_params)

def interweave(a, b):
    c = np.empty((a.size + b.size,), dtype=a.dtype)
    c[0::2] = a
    c[1::2] = b
    return c

if __name__ == '__main__':
    hf = h5py.File('/scratch0/ilya/locDoc/data/hyperspec/features/np_data.h5', 'w')
    # see http://christopherlovell.co.uk/blog/2016/04/27/h5py-intro.html

    Mss = np.array([[9,9,4], [9,9,16], [9,9,4]])
    strides = np.array([[1,1,4], [1,1,16], [1,1,4]])
    H, W, D = 1096, 492, 102
    hyper = autograd.Variable(torch.randn(1, 1, H, W, D).type(dtype))
    Phi = np.empty((H, W, ), dtype='single')

    paddings = int(np.ceil((Mss - 1) / 2.))

    # prepare filters
    winO1 = gabor_window_factory_3D(Mss[1,:])
    catfilt = interweave(winO1.filters.real, winO1.filters.imag)
    M1filt = autograd.Variable(torch.from_numpy(catfilt).type(dtype))
    winO2 = gabor_window_factory_3D(Mss[2,:])
    catfilt = interweave(winO2.filters.real, winO2.filters.imag)
    M2filt = autograd.Variable(torch.from_numpy(catfilt).type(dtype))
    winO3 = gabor_window_factory_3D(Mss[3,:])
    catfilt = np.concatenate((winO3.filters[0,:,:,:,:].real, winO3.filters[0,:,:,:,:].imag))
    M3filt = autograd.Variable(torch.from_numpy(catfilt).type(dtype))

    for i in range(0, win01.nfilt):
        i1 = (i*2);
        i2 = i1 + 2;
        tmp1 = F.conv3d(hyper, M1filt[i1:i2,:,:,:,:], None, strides[0,:], paddings[0,:])
        tmp1 = tmp1 * tmp1;
        pdb.set_trace()
        out1 = torch.sum(tmp1, dim=1)
        del tmp1
        if i == 0:
            np.append(Phi, out1.numpy(), axis=3)
            del out1
        else:
            for j in range(0, win02.nfilt):
                j1 = (j*2);
                j2 = j1 + 2;
                tmp2 = F.conv3d(out1, M2filt[j1:j2,:,:,:,:], None, strides[1,:], paddings[1,:])
                tmp2 = tmp2 * tmp2;
                out2 = torch.sum(tmp2, dim=1)
                del tmp2
                if j == 0:
                    np.append(Phi, out2.numpy(), axis=3)
                    del out2
                else:
                    tmp3 = F.conv3d(out2, M3filt, None, strides[2,:], paddings[2,:])
                    tmp3 = tmp3 * tmp3;
                    out3 = torch.sum(tmp3, dim=1)
                    del tmp3
                    np.append(Phi, out3.numpy(), axis=3)
                    del out3

    hf.create_dataset('feats', data=Phi)
    hf.close()

# if __name__ == '__main__':

#     catfilt = np.concatenate((winO.filters.real, winO.filters.imag))

#     filters = autograd.Variable(torch.from_numpy(catfilt[0:75, :,:,:,:]).type(dtype))

#     H, W, D = 1096, 492, 102

#     inputs = autograd.Variable(torch.randn(1, 1, H, W, D).type(dtype))
#     start = time.time()
#     out = F.conv3d(inputs, filters, None, (1, 1, 4), (4, 4, 2))
#     end = time.time()
#     print(end - start)
#     print('done')
