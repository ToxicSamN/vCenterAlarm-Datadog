
import base64
from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP
from vcenterdd.log.setup import addClassLogger


@addClassLogger
class PKCS7Encoder(object):
    '''
    Author: jeppeter Wang
    Author-email: jeppeter@gmail.com

    RFC 2315: PKCS#7 page 21
    Some content-encryption algorithms assume the
    input length is a multiple of k octets, where k > 1, and
    let the application define a method for handling inputs
    whose lengths are not a multiple of k octets. For such
    algorithms, the method shall be to pad the input at the
    trailing end with k - (l mod k) octets all having value k -
    (l mod k), where l is the length of the input. In other
    words, the input is padded at the trailing end with one of
    the following strings:
             01 -- if l mod k = k-1
            02 02 -- if l mod k = k-2
                        .
                        .
                        .
          k k ... k k -- if l mod k = 0
    The padding can be removed unambiguously since all input is
    padded and no padding string is a suffix of another. This
    padding method is well-defined if and only if k < 256;
    methods for larger k are an open issue for further study.
    but we have the value
    '''
    def __init__(self, k=16, offset=0):
        assert(k <= 256)
        assert(k > 1)
        self.__klen = k
        self.offset = offset

    ## @param text The padded text for which the padding is to be removed.
    # @exception ValueError Raised when the input padding is missing or corrupt.
    def decode(self, text):
        dectext = ''
        if (len(text) % self.__klen) != 0:
            raise Exception('text not %d align' % (self.__klen))
        lastch = ord(text[-1])
        if lastch <= self.__klen and lastch != 0:
            trimlen = lastch
            textlen = len(text)
            for i in range(lastch):
                if ord(text[textlen - i - 1]) != lastch:
                    trimlen = 0
                    break
            if trimlen == 0:
                dectext = text
            else:
                dectext = text[:(textlen - trimlen)]
        else:
            dectext = text
        return dectext

    def get_bytes(self, text):
        outbytes = []
        for c in text:
            outbytes.append(ord(c))
        return outbytes

    def get_text(self, inbytes):
        s = ''
        for i in inbytes:
            s += chr((i % 256))
        return s

    def __encode_inner(self, text):
        '''
        Pad an input string according to PKCS#7
        if the real text is bits same ,just expand the text
        '''
        totallen = len(text)
        passlen = 0
        enctext = ''
        if (len(text) % self.__klen) != 0:
            enctext = text
            leftlen = self.__klen - (len(text) % self.__klen)
            lastch = chr(leftlen)
            enctext += lastch * leftlen
        else:
            lastch = ord(text[-1])
            if lastch <= self.__klen and lastch != 0:
                trimlen = self.__klen
                textlen = len(text)
                for i in range(lastch):
                    if lastch != ord(text[(textlen - i - 1)]):
                        trimlen = 0
                        break
                if trimlen == 0:
                    enctext = text
                else:
                    enctext = text
                    enctext += chr(self.__klen) * self.__klen
            else:
                enctext = text

        return enctext

    ## @param text The text to encode.
    def encode(self, text):
        return self.__encode_inner(text)


@addClassLogger
class AESCipher(object):
    """
        Custom class for creating a AES Cipher for encryption/decryption processing
        By default this uses AES Cipher Mode CFB. this is built for specific purpose and not
        designed to be used with all AES Cipher Modes.
    """
    def __init__(self):
        self.AES_BLOCK_SIZE = AES.block_size
        self.AES_KEY = Random.get_random_bytes(32)
        self.__log.debug("AES_KEY: {}".format(self.AES_KEY))
        self.__log.debug("AES_BLOCK_SIZE: {}".format(self.AES_BLOCK_SIZE))
        self.padding = PKCS7Encoder()
        self.decrypted_bytes = None
        self.decrypted_data = None

    def encrypt(self, raw, *args, **kwargs):
        try:
            if isinstance(raw, str):
                self.__log.debug("raw text is 'str'. convert to bytes")
                tmp = self.padding.encode(raw).encode('utf')
                self.__log.debug(tmp)
            else:
                raise ValueError("data to be encrypted is not in 'str' form")

            if kwargs.get('IV' or None):
                kwargs['IV'] = Random.get_random_bytes(self.AES_BLOCK_SIZE)
            else:
                kwargs.update({'IV': Random.get_random_bytes(self.AES_BLOCK_SIZE)})

            self.__log.debug("AES_IV: {}".format(kwargs['IV']))
            self.__log.debug('IV_Size kwargs: {}'.format(len(kwargs['IV'])))
            self.__log.debug('Creating AES Cipher')
            cipher = AES.new(key=self.AES_KEY,
                             mode=AES.MODE_CFB,
                             **kwargs)
            self.__log.debug('IV_Size cipher: {}'.format(len(cipher.IV)))
            ciphertext = cipher.encrypt(tmp)
            self.__log.debug("ciphertext: {}".format(ciphertext))
            return base64.b64encode(kwargs['IV'] + ciphertext)

        except BaseException as e:
            self.__log.exception('Exception: {} \n Args: {}'.format(e, e.args))
            raise e

    def decrypt(self, enc, key, *args, **kwargs):
        if key:
            if isinstance(key, str):
                self.AES_KEY = base64.b64decode(key)
            else:
                self.AES_KEY = key
        self.__log.debug("Encrypted text: {}".format(enc))
        enc = base64.b64decode(enc)

        if kwargs.get('IV' or None):
            kwargs['IV'] = enc[:self.AES_BLOCK_SIZE]
        else:
            kwargs.update({'IV': enc[:self.AES_BLOCK_SIZE]})
        self.__log.debug("AES_IV: {}".format(kwargs['IV']))
        self.__log.debug('IV_Size: {}'.format(len(kwargs['IV'])))
        self.__log.debug('Creating AES Cipher')
        cipher = AES.new(self.AES_KEY, AES.MODE_CFB, **kwargs)
        self.__log.debug('IV_Size: {}'.format(len(cipher.IV)))
        self.decrypted_bytes = cipher.decrypt(enc[self.AES_BLOCK_SIZE:])
        ciphertext = self.padding.get_text(self.decrypted_bytes)
        return self.padding.decode(ciphertext)
