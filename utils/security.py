"""
File performs the security checks and validate the user provided information
"""
import hashlib
import hmac
import math
import random
import re
import string
import struct

import bcrypt


class Security(object):
    # var string The cipher to use for encryption and decryption.
    cipher = 'AES-128-CBC'

    # @var array[] Look-up table of block sizes and key sizes for each supported OpenSSL cipher.
    # In each element, the key is one of the ciphers supported by OpenSSL (@see openssl_get_cipher_methods()).
    # The value is an array of two integers, the first is the cipher's block size in bytes and the second is
    # the key size in bytes.
    #
    # > Warning: All OpenSSL ciphers that we recommend are in the default value, i.e. AES in CBC mode.
    #
    # > Note: encryption protocol uses the same size for cipher key, HMAC signature key and key
    # derivation salt.
    hmac = hmac
    allowed_ciphers = {
        'AES-128-CBC': [16, 16],
        'AES-192-CBC': [16, 24],
        'AES-256-CBC': [16, 32],
    }
    # var string Hash algorithm for key derivation. Recommend sha256, sha384 or sha512.
    kdf_hash = 'sha256'

    # string Hash algorithm for message authentication. Recommend sha256, sha384 or sha512.
    mac_hash = 'sha256'

    # string HKDF info value for derivation of message authentication key.

    auth_key_info = 'AuthorizationKey'

    # integer derivation iterations count.
    # Set as high as possible to hinder dictionary password attacks.
    derivation_iterations = 100000

    #   string strategy, which should be used to generate password hash.
    #   Available strategies:
    #   - 'password_hash' - use of PHP `password_hash()` function with PASSWORD_DEFAULT algorithm.
    #     This option is recommended, but it requires PHP version >= 5.5.0
    #   - 'crypt' - use PHP `crypt()` function.

    password_hash_strategy = 'crypt'

    def mb_strlen(self, string, encoding='utf-8'):
        return len(string.decode(encoding))

    def encrypt(self, data, password_based, secret, info):
        """
        Encrypts data.

        :param str data:
        :param bool password_based:
        :param str secret:
        :param str info:
        :return:(return string the encrypted data
                throws Exception on OpenSSL not loaded
                throws Exception on OpenSSL error )
        """

        # if not extension_loaded('openssl'):
        #     raise Exception('Encryption requires the OpenSSL PHP extension')

        if not (self.allowed_ciphers[self.cipher][0], self.allowed_ciphers[self.cipher][1]):
            raise Exception(self.cipher + ' is not an allowed cipher')

        [block_size, key_size] = self.allowed_ciphers[self.cipher]

        key_salt = self.generate_random_key(key_size)
        if password_based:
            key = self.pbkdf2(self.kdf_hash, secret, key_salt, self.derivation_iterations, key_size)
        else:
            key = self.hkdf(self.kdf_hash, secret, key_salt, info, key_size)

        iv = self.generate_random_key(block_size)
        #
        # encrypted = openssl_encrypt(data, self.cipher, key, OPENSSL_RAW_DATA, iv)
        # if not encrypted:
        #     raise Exception('OpenSSL failure on encryption: ' + openssl_error_string())

        auth_key = self.hkdf(self.kdf_hash, key, '', self.auth_key_info, key_size)
        hashed = self.hash_data(iv, auth_key)

        return key_salt + hashed

    def encrypt_by_password(self, data, password):
        return self.encrypt(data, True, password, '')

    def encrypt_by_key(self, data, input_key, info=None):
        """
        Encrypts data using a cryptograhic key.
        Derives keys for encryption and authentication from the input key using HKDF and a random salt,
        which is very fast relative to [[encryptByPassword()]]. The input key must be properly
        random -- use [[generateRandomKey()]] to generate keys.
        The encrypted data includes a keyed message authentication code (MAC) so there is no need
        to hash input or output data.
        :param str data: the data to encrypt
        :param str input_key: the input to use for encryption and authentication
        :param str info: optional context and application specific information, see [[hkdf()]]
        :return: the encrypted data
        :rtype: str
        """
        return self.encrypt(data, False, input_key, info)

    def decrypt_by_password(self, data, password):
        """
        Verifies and decrypts data encrypted with [[encryptByPassword()]].
        :param str data: the encrypted data to decrypt
        :param str password: the password to use for decryption
        :rtype: bool
        :return: string the decrypted data or false on authentication failure
        """
        return self.decrypt(data, True, password, '')

    def decrypt_by_key(self, data, inputKey, info=None):
        """
        Verifies and decrypts data encrypted with [[encryptByPassword()]].
        :param str data: the encrypted data to decrypt
        :param str inputKey: the input to use for encryption and authentication
        :param str info: optional context and application specific information, see [[hkdf()]]
        :rtype: bool
        :return: the decrypted data or false on authentication failure
        """
        return self.decrypt(data, False, inputKey, info)

    def hkdf(self, algo, input_key, salt=None, info=None, length=0):
        """
        Derives a key from the given input key using the standard HKDF algorithm.
        Implements HKDF specified in [RFC 5869](https://tools.ietf.org/html/rfc5869).
        Recommend use one of the SHA-2 hash algorithms: sha224, sha256, sha384 or sha512.

        :param str algo: a hash algorithm supported by `hash_hmac()`, e.g. 'SHA-256'
        :param str input_key: the source key
        :param str salt: the random salt
        :param str info: optional info to bind the derived key material to application and context-specific information,
                e.g. a user ID or API version
        :param int length:
        :rtype: str
        :return:the derived key
        """
        test = self.hmac.new(algo, '', '')
        if not test:
            raise Exception('Failed to generate HMAC with hash algorithm: ' + algo)

        hash_length = len(str(test))
        if type(length) is str and re.search('{^\d{1,16}}', str(length)):
            length = int(length)

        if not type(length) is int or length < 0 or length > 255 * hash_length:
            raise Exception('Invalid length')

        if length != 0:
            blocks = math.ceil(length / hash_length)
        else:
            blocks = 1
        if not salt:
            salt = "\0"  # hash_length

        pr_key = self.hmac.new(algo, input_key, salt)

        hmac = ''
        output_key = ''
        for i in range(blocks):
            hmac = self.hmac.new(algo, hmac + info + (i), pr_key)
            output_key += hmac

        if length != 0:
            output_key = self.mb_substr(output_key.encode('utf-8'), 0, length)

        return output_key

    def decrypt(self, data, password_based, secret, info):
        """
        Decrypts data

        :param str data: encrypted data to be decrypted.
        :param bool password_based: set true to use password-based key derivation
        :param str secret: the decryption password or key
        :param str info: context/application specific information, @see encrypt()
        :return:    (bool|string the decrypted data or false on authentication failure
                    throws Exception on OpenSSL not loaded
                    throws Exception on OpenSSL error)
        """
        # if not extension_loaded('openssl'):
        #     raise Exception('Encryption requires the OpenSSL PHP extension')

        if not (self.allowed_ciphers[self.cipher][0], self.allowed_ciphers[self.cipher][1]):
            raise Exception(self.cipher + ' is not an allowed cipher')

        [block_size, key_size] = self.allowed_ciphers[self.cipher]

        key_salt = self.mb_substr(data.encode('utf-8'), 0, key_size)
        if password_based:
            key = self.pbkdf2(self.kdf_hash, secret, key_salt, self.derivation_iterations, key_size)
        else:
            key = self.hkdf(self.kdf_hash, secret, key_salt, info, key_size)

        authKey = self.hkdf(self.kdf_hash, key, '', self.auth_key_info, key_size)
        data = self.validate_data(self.mb_substr(data.encode('utf-8'), start=0, length=key_size), authKey)

        if not data:
            return False

        # iv = self.mb_substr(data.encode('utf-8'), 0, block_size)
        # encrypted = self.mb_substr(data.encode('utf-8'),block_size, 0)
        #
        # decrypted = openssl_decrypt(encrypted, self.cipher, key, OPENSSL_RAW_DATA, iv)
        #
        # if not decrypted:
        #     raise Exception('OpenSSL failure on decryption: ' + openssl_error_string())

        return data

    def pbkdf2(self, algo, password, salt, iterations, length=0):
        """
        Derives a key from the given password using the standard PBKDF2 algorithm.
        Implements HKDF2 specified in [RFC 2898](http://tools.ietf.org/html/rfc2898#section-5.2)
        Recommend use one of the SHA-2 hash algorithms: sha224, sha256, sha384 or sha512.
        :param str algo: a hash algorithm supported by `hash_hmac()`, e.g. 'SHA-256'
        :param str password: the source password
        :param str salt: the random salt
        :param int iterations: the number of iterations of the hash algorithm. Set as high as
                possible to hinder dictionary password attacks.
        :param int length: length of the output key in bytes. If 0, the output key is
                t   he length of the hash algorithm output.
        :return: ((string the derived key
                throws Exception when hash generation fails due to invalid params given.))
        """
        # if (function_exists('hash_pbkdf2')):
        #     output_key = pbkdf2_sha256(algo, password, salt, iterations, length, True)
        #     if not output_key:
        #         raise Exception('Invalid parameters to hash_pbkdf2()')
        #     return output_key

        # todo: is there a nice way to reduce the code repetition in hkdf() and pbkdf2()?
        test = self.hmac.new(algo, '', '')
        if not test:
            raise Exception('Failed to generate HMAC with hash algorithm: ' + algo)

        if type(iterations) is str and re.search('{^\d{1,16}}', str(iterations)):
            iterations = int(iterations)

        if not type(iterations) is int or iterations < 1:
            raise Exception('Invalid iterations')

        if type(length) is str and re.search('{^\d{1,16}}', str(length)):
            length = int(length)

        if not type(length) is int or length < 0:
            raise Exception('Invalid length')

        hash_length = self.mb_strlen(test)

        if length != 0:
            blocks = math.ceil(length / hash_length)
        else:
            blocks = 1

        output_key = ''
        for j in range(blocks):
            string = struct.pack('N', j)
            string += salt
            hash_mac = self.hmac.new(algo, string, password)
            xorsum = hash_mac
            for i in range(iterations):
                hmac = self.hmac.new(algo, hash_mac, password)
                xorsum ^= hmac
            output_key += xorsum

        if length != 0:
            output_key = self.mb_substr(output_key.encode('utf-8'), 0, length)

        return output_key

    def hash_data(self, data, key, raw_hash=False):
        """
        Prefixes data with a keyed hash value so that it can later be detected if it is tampered.
        There is no need to hash inputs or outputs of [[encryptByKey()]] or [[encryptByPassword()]]
        as those methods perform the task.
        :param str data: the data to be protected
        :param str key: the secret key to be used for generating hash. Should be a secure cryptographic key.
        :param bool raw_hash: whether the generated hash value is in raw binary format. If false, lowercase hex digits
                will be generated.
        :return: (string the data prefixed with the keyed hash
                    throws Exception when HMAC generation fails.)
        """
        hash = self.hmac.new(key=key, msg=data, digestmod=self.mac_hash)
        if raw_hash:
            hash = hash.digest()
        else:
            hash = hash.hexdigest()
        if not hash:
            raise Exception('Failed to generate HMAC with hash algorithm: ' + self.mac_hash)

        return hash + data

    def validate_data(self, data, key, raw_hash=False):
        """
        Validates if the given data is tampered.
        :param str data: the data to be validated. The data must be previously generated by [[hashData()]].
        :param str key:  the secret key that was previously used to generate the hash for the data in [[hashData()]].
                         function to see the supported hashing algorithms on your system. This must be the same as the
                         value passed to [[hashData()]] when generating the hash for the data.
        :param bool raw_hash:   this should take the same value as when you generate the data using [[hashData()]].
                                It indicates whether the hash value in the data is in binary format. If false, it means
                                the hash value consist of lowercase hex digits only.
        :return:    (the real data with the hash stripped off. False if the data is tampered.
                    throws Exception when HMAC generation fails.)
        """
        test = self.hmac.new(self.mac_hash, '', '')
        if not test:
            raise Exception('Failed to generate HMAC with hash algorithm: ' + self.mac_hash)

        hash_length = self.mb_strlen(test)
        if self.mb_strlen(data.encode('utf-8')) >= hash_length:
            hash = self.mb_substr(data.encode('utf-8'), 0, hash_length)
            pure_data = self.mb_substr(data.encode('utf-8'), hash_length, 0)

            calculated_hash = self.hmac.new(self.mac_hash, pure_data, key)

            if self.compare_string(hash, calculated_hash):
                return pure_data
        return False

    def generate_salt(self, cost=13):
        """
        Generates the salt
        :param int cost: value used in salt
        :return: str generated salt
        """

        cost = int(cost)
        if cost < 4 or cost > 31:
            raise Exception('Cost must be between 4 and 31.')

        # Get a 20-byte random string
        rand = self.generate_random_string(20)
        # Form the prefix that specifies Blowfish (bcrypt) algorithm and cost parameter.

        salt = "$2y$%s$" % cost

        # Append the random salt data in the required base64 format.
        value = (''.join((random.choice(rand)) for x in range(22)))
        value = value.replace("h", ".")
        value = value.replace("9", "/")
        salt += value
        return salt

    def validate_password(self, password, hash_value):
        """
        Verifies a password against a hash.
        :param password: The password to verify.
        :param hash_value: The hash to verify the password against.
        :rtype: bool
        :return: whether the password is correct.
        """
        if not type(password) is str or password == '':
            raise Exception('Password must be a string and cannot be empty.')

        if self.password_hash_strategy == 'password_hash':
            # if (!function_exists('password_verify')) {
            #     throw new Exception('Password hash key strategy "password_hash" requires PHP >= 5.5.0, either upgrade
            # your environment or use another strategy.');
            # }
            # return password_verify(password, hash);
            pass
        try:
            # checking the password hash strategy
            if self.password_hash_strategy == 'crypt':
                password = password.encode('utf-8')
                hash_value = hash_value.encode('utf-8')
                test = bcrypt.hashpw(password, hash_value)
                n = len(test)
                if n != 60:
                    return False
                return self.compare_string(test, hash_value)
            else:
                raise Exception("Unknown password hash strategy " + self.password_hash_strategy)
        except:
            return False

    def generate_password_hash(self, password, cost=13):
        """
        Generates the hashed password
        :param str password: password provided
        :param int cost: value provided
        :return: hashed password
        """
        if self.password_hash_strategy == 'password_hash':
            # if (!function_exists('password_verify')) {
            #     throw new Exception('Password hash key strategy "password_hash" requires PHP >= 5.5.0, either upgrade
            #  your environment or use another strategy.');
            # }
            # return password_verify(password, hash);
            pass

        if self.password_hash_strategy == 'crypt':
            salt = self.generate_salt(cost)
            salt = salt.encode(encoding='utf-8')
            password = password.encode(encoding='utf-8')
            hash = bcrypt.hashpw(password, salt)
            hash = str(hash)
            hash = hash[2:62]
            if len(hash) != 60:
                raise Exception('Unknown error occurred while generating hash.')

            return hash
        else:
            raise Exception("Unknown password hash strategy " + self.password_hash_strategy)

    @staticmethod
    def hash_value(data):
        """
        Returns the md5 hashed value
        :param data: password_haseh
        :return: hashed_value
        """
        data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()

    def validate_hash_magento(self, password, _hash):
        """
        validate magento customer's password
        :param str password: password of user
        :param str _hash: hashed value from db
        :rtype: bool
        """
        hash_arr = _hash.split(':')
        try:
            if hash_arr[1]:
                # if user verified, then updating the password hash of user according to
                # blow fish algorithm.
                if self.hash_value(hash_arr[1] + password) == hash_arr[0]:
                    from repositories.customer_repo import CustomerProfile
                    new_hash = self.generate_password_hash(password=password)
                    return CustomerProfile().insert_new_password_hash_of_user(
                        _hash=_hash,
                        new_hash=new_hash
                    )
        except:
            pass
        return False

    @staticmethod
    def mb_substr(s, start, length=None, encoding="UTF-8"):
        """

        :param  s:
        :param int start:
        :param int length:
        :param str encoding:
        :return:
        """
        # if not length:
        #     self.mb_strlen(s)
        # else:
        #
        u_s = s.decode(encoding)
        return (u_s[start:(start + length)] if length else u_s[start:]).encode(encoding)

    @staticmethod
    def generate_random_key(length=32):
        """
        Generates the random ket
        :param length: string to be created of length
        :return: randomly generated string
        """
        random_string = string.ascii_letters + string.punctuation
        return ''.join((random.choice(random_string)) for x in range(length))

    @staticmethod
    def generate_random_string(length=32):
        """
        Generates random string
        :param length: length of the string
        :return:
        """
        random_string = string.ascii_letters + string.digits
        return ''.join((random.choice(random_string)) for x in range(length))

    @staticmethod
    def compare_string(str1, str2):
        """
        Compares the strings
        :param str str1: string one
        :param str str2: string two to compare
        :return: bool value
        """
        if str1 == str2:
            return True
        else:
            return False


security = Security()
