# #!/usr/bin/python
# # -*- coding: utf-8 -*-
# ##############################################################################
# #
# #    Copyright (C) 2009 ADSOFT - OpenERP Partner Indonesia
# #
# #    This program is free software: you can redistribute it and/or modify
# #    it under the terms of the GNU General Public License as published by
# #    the Free Software Foundation, either version 3 of the License, or
# #    (at your option) any later version.
# #
# #    This program is distributed in the hope that it will be useful,
# #    but WITHOUT ANY WARRANTY; without even the implied warranty of
# #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #    GNU General Public License for more details.
# #
# #    You should have received a copy of the GNU General Public License
# #    along with this program.  If not, see <http://www.gnu.org/licenses/>.
# #
# ##############################################################################

# sym={
#     "en": {
#         "sep": " ",
#         "0": "zero",
#         "x": ["one","two","three","four","five" ,"six","seven","eight","nine"],
#         "1x": ["ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"],
#         "x0": ["twenty","thirty","fourty","fifty","sixty","seventy","eighty","ninety"],
#         "100": "hundred",
#         "1K": "thousand",
#         "1M": "million",
#         "1B": "billion",
#         "1T": "trillion",    
#     },
#     "id": {
#         "sep": " ",
#         "0": "nol",
#         "x": ["satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"],
#         "1x": ["sepuluh", "sebelas", "dua belas", "tiga belas", "empat belas", "lima belas", "enam belas", "tujuh belas", "delapan belas", "sembilan belas"],
#         "x0": ["dua puluh", "tiga puluh", "empat puluh", "lima puluh", "enam puluh", "tujuh puluh", "delapan puluh", "sembilan puluh"],
#         "10": "puluh",
#         "x00": "ratus",
#         "100": "seratus",
#         "1K": "ribu",
#         "1M": "juta",
#         "1B": "milliar",
#         "1T": "trilliun",    
#     }
# }

# def num2word(n,l="en"):
#     #TODO:Support Thai Stang 
#     if n==0:
#         return sym[l]["0"] + " "
#     elif n<10:
#         return sym[l]["x"][n-1]
#     elif n<100:
#         if l=="en":
#             if n<20:
#                 return sym[l]["1x"][n-10]
#             else:
#                 return sym[l]["x0"][n/10-2]+(n%10 and sym[l]["sep"]+num2word(n%10,l) or "")
#         elif l=="th":
#             return sym[l]["x0"][n/10-1]+(n%10 and (n%10==1 and sym[l]["x1"] or sym[l]["x"][n%10-1]) or "")
#     elif n<1000:
#         return sym[l]["x"][n/100-1]+sym[l]["sep"]+sym[l]["100"]+(n%100 and sym[l]["sep"]+num2word(n%100,l) or "")
#     elif n<1000000:
#         if l=="en":
#             return num2word(n/1000,l)+sym[l]["sep"]+sym[l]["1K"]+(n%1000 and sym[l]["sep"]+num2word(n%1000,l) or "")
#         elif l=="th":
#             if n<10000:
#                 return sym[l]["x"][n/1000-1]+sym[l]["1K"]+(n%1000 and num2word(n%1000,l) or "")
#             elif n<100000:
#                 return sym[l]["x"][n/10000-1]+sym[l]["10K"]+(n%1000 and num2word(n%10000,l) or "")
#             else:
#                 return sym[l]["x"][n/100000-1]+sym[l]["100K"]+(n%10000 and num2word(n%100000,l) or "")
#     elif n<1000000000:
#         return num2word(n/1000000,l)+sym[l]["sep"]+sym[l]["1M"]+sym[l]["sep"]+(n%1000000 and num2word(n%1000000,l) or "")
#     else:
#         return "N/A"

# def num2word_id(n,l="en"):
#     base=0
#     end=0
#     number = '%.2f'%n
#     number = str(number).split('.')
#     base = num2word(int(number[0]),l=l)
#     if int(number[1])!=0:
#         end = num2word(int(number[1]),l=l)
#     if base==0 and end==0:
#         word=''
#     if base!=0 and end==0:
#         word=base
#     if base!=0 and end!=0:
#         word=base
#     word = word[:1].upper()+word[1:].lower()
#     return word
    
# if __name__ == '__main__':
#     import sys
#     n=sys.stdin.readline()
#     print num2word_id(n)

sym={
    "en": {
        "sep": " ",
        "0": "zero",
        "x": ["one","two","three","four","five" ,"six","seven","eight","nine"],
        "1x": ["ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"],
        "x0": ["twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"],
        "100": "hundred",
        "1K": "thousand",
        "1M": "million",
        "1B": "billion",
        "1T": "trillion",    
    },
    "id": {
        "sep": " ",
        "0": "nol",
        "x": ["satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"],
        "1x": ["sepuluh", "sebelas", "dua belas", "tiga belas", "empat belas", "lima belas", "enam belas", "tujuh belas", "delapan belas", "sembilan belas"],
        "x0": ["dua puluh", "tiga puluh", "empat puluh", "lima puluh", "enam puluh", "tujuh puluh", "delapan puluh", "sembilan puluh"],
        "10": "puluh",
        "x00": "ratus",
        "100": "seratus",
        "1000":"seribu",
        "1K": "ribu",
        "1M": "juta",
        "1B": "milliar",
        "1T": "trilliun",    
    }
}

def num2word(n,l):
    #TODO:Support Thai Stang 
    if n==0:
        return sym[l]["0"] + " "
    elif n<10:
        return sym[l]["x"][n-1]
    elif n<100:
        # if l=="id":
        if n<20:
            return sym[l]["1x"][n-10]
        else:
            return sym[l]["x0"][n/10-2]+(n%10 and sym[l]["sep"]+num2word(n%10,l) or "")
    elif n<1000:
        if l=="id":
            if n<200:
                return sym[l]["100"]+(n%100 and sym[l]["sep"]+num2word(n%100,l) or "")
            else:
                return sym[l]["x"][n/100-1]+sym[l]["sep"]+sym[l]["x00"]+(n%100 and sym[l]["sep"]+num2word(n%100,l) or "")
        elif l=="en":
            return sym[l]["x"][n/100-1]+sym[l]["sep"]+sym[l]["100"]+(n%100 and sym[l]["sep"]+num2word(n%100,l) or "")
    elif n<1000000:
        if l=="id":
            if n<2000:
                return sym[l]["1000"]+(n%1000 and sym[l]["sep"]+num2word(n%1000,l) or "")
            else:
                return num2word(n/1000,l)+sym[l]["sep"]+sym[l]["1K"]+(n%1000 and sym[l]["sep"]+num2word(n%1000,l) or "")
        elif l=="en":
            return num2word(n/1000,l)+sym[l]["sep"]+sym[l]["1K"]+(n%1000 and sym[l]["sep"]+num2word(n%1000,l) or "")
    elif n<1000000000:
        return num2word(n/1000000,l)+sym[l]["sep"]+sym[l]["1M"]+sym[l]["sep"]+(n%1000000 and num2word(n%1000000,l) or "")
    elif n<1000000000000:
        return num2word(n/1000000000,l)+sym[l]["sep"]+sym[l]["1B"]+sym[l]["sep"]+(n%1000000000 and num2word(n%1000000000,l) or "")
    else:
        return "N/A"

def num2word_id(n,l="id"):
    print ">>", l
    base=0
    end=0
    number = '%.2f'%n
    number = str(number).split('.')
    base = num2word(int(number[0]),l=l)
    if int(number[1])!=0:
        end = num2word(int(number[1]),l=l)
    if base==0 and end==0:
        word=''
    if base!=0 and end==0:
        word=base
    if base!=0 and end!=0:
        if l=="id":
            word=base + " koma "+ end
        elif l=="en":
            word=base + " point "+end
    
    word = word[:1].upper()+word[1:].lower()
    return word
    
if __name__ == '__main__':
    import sys
    n=sys.stdin.readline()
    print num2word_id(n)

