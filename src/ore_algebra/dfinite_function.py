# coding: utf-8
"""
dfinite_function
================

The dfinite_function package provides functionality for doing computations with D-finite functions and sequences.

A D-finite sequence can be represented by an ore operator which annihilates the sequence (for further information
about ore operators check the ``ore_algebra`` package), the operators singularities and a finite amount of initial values.

A D-finite function can be envisioned as a power series, therefore it can be represented via a D-finite sequence which
describes the coefficient sequence and an ore operator which annhilates the function.

D-finite sequences and functions are elements of D-finite function rings. D-finite function rings are ring objects created by the
function ``DFiniteFunctionRing`` as described below.

Depending on the particular parent ring, D-finite functions/sequences may support different functionality.
For example, for D-finite sequences, there is a method for computing an interlacing sequence, an operation 
which does not make sense for D-finite functions.
However basic arithmetic, such as addition and multiplication is implemented for both cases.

AUTHOR:

- Manuel Kauers, Stephanie Schwaiger, Clemens Hofstadler (2017-07-15)

"""

#############################################################################
#  Copyright (C) 2017 Manuel Kauers (mkauers@gmail.com),                    #
#                     Stephanie Schwaiger (stephanie.schwaiger97@gmail.com),#
#                     Clemens Hofstadler (clemens.hofstadler@liwest.at).    #
#                                                                           #
#  Distributed under the terms of the GNU General Public License (GPL)      #
#  either version 2, or (at your option) any later version                  #
#                                                                           #
#  http://www.gnu.org/licenses/                                             #
#############################################################################

from __future__ import absolute_import

from .ore_algebra import OreAlgebra
from .dfinite_symbolic import symbolic_database
from .guessing import guess

from sage.rings.ring import Algebra
from sage.structure.element import RingElement
from numpy import random
from math import factorial
from operator import pow
from sage.symbolic.operators import add_vararg, mul_vararg
from sage.rings.semirings.non_negative_integer_semiring import NN
from sage.rings.integer_ring import ZZ
from sage.rings.rational_field import QQ
from sage.misc.prandom import randint
from sage.calculus.var import var
from sage.matrix.constructor import matrix

from sage.all import *


class DFiniteFunctionRing(Algebra):
    """
    A Ring of Dfinite objects (functions or sequences)
    """
    
    _no_generic_basering_coercion = False

# constructor
    
    def __init__(self, ore_algebra, codomain = NN, name=None, element_class=None, category=None):
        """
        Constuctor for a D-finite function ring.
        
        INPUT:
        
        - ``ore_algebra`` -- an Ore algebra over which the D-finite function ring is defined.
            Only ore algebras with the differential or the shift operator are accepted to
            define a D-finite function ring.
        - ``codomain`` (default ``NN``) -- domain over which the sequence indices are considered,
            i.e. if the codomain is ``ZZ``also negative sequence inidices exist.
            So far for d-finite sequences ``NN`` and ``ZZ`` are supported and for D-finite
            functions only ``NN``is supported.
        
        OUTPUT:
        
        A ring of either D-finite sequences or functions
            
        EXAMPLES::
        
            sage: from ore_algebra import *
            sage: load("dfinite_function.py")
            
            #This creates an d-finite sequence ring with indices in ``ZZ``
            sage: A = OreAlgebra(ZZ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: D
            Ring of D-finite sequences over Univariate Polynomial Ring in n over Integer Ring
            
            #This creates an d-finite function ring
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: E = DFiniteFunctionRing(B)
            sage: E
            Ring of D-finite functions over Univariate Polynomial Ring in x over Rational Field

        """
        if codomain != ZZ and codomain != NN:
            raise TypeError, "Codomain does not fit"
        
        self._ore_algebra = ore_algebra
        self._base_ring = ore_algebra.base_ring()
        
        if ore_algebra.is_D() and codomain == ZZ:
            raise NotImplementedError, "D-finite functions with negative powers are not implemented"
        self._codomain = codomain
        if codomain == NN:
            self._backward_calculation = False
        else:
            self._backward_calculation = true
    
#conversion

    def _element_constructor_(self, x=None, check=True, is_gen = False, construct=False, **kwds):
        r"""
        Convert ``x`` into this ring, possibly non-canonically.
        
        This is possible if:
        
        - ``x``is already a d-finite object. Then it is converted into the new d-finite function ring if possible. See the
          method ``_construct_dfinite`` for further information
        - ``x`` is a list of data. Then it is interpreted as the first coefficients of
          a sequence or a power series and the method ``guess``is called in order to
          find a suitable Ore Operator. See  the method ``_construct_list`` for further information
        - ``x`` can be converted into a rational number. Then it is intpreted as the constant sequence 
           x,x,x,\dots or the constant function f(z) = x depending on the D-finite function ring.
        - ``x``can be converted into the fraction field of the base ring of the D-finite function ring. Then it is interpreted as
          the sequence (a_n) := x(n) for the recurrence case or as the function f(z) = x(z) for the
          differential case. See the method ``_construct_rational`` for further information
        - ``x`` is a symbolic expression. Then ``x``is decomposed into atomic expressions which are then converted to D-finite objects if possible
          and put back together. See ``_construct_symbolic`` for further information.
        
        EXAMPLES::
    
        sage: A = OreAlgebra(QQ['n'],'Sn')
        sage: D1 = DFiniteFunctionRing(A)
        sage: B = OreAlgebra(QQ['x'],'Dx')
        sage: D2 = DFiniteFunctionRing(B)
        sage: n = A.base_ring().gen()
        sage: x = B.base_ring().gen()
        
        #conversion of a list of data
        sage: D1([0,1,1,2,3,5,8,13])
        Univariate D-finite sequence defined by the annihilating operator -Sn^2 + Sn + 1 and the initial conditions {0: 0, 1: 1}
        sage: D2([1,-1,1,-1,1,-1])
        Univariate D-finite function defined by the annihilating operator (x + 1)*Dx + 1 and the coefficient sequence defined by (n + 1)*Sn + n + 1 and {0: 1}
        
        #conversion of rational numbers
        sage: D1(3)
        Univariate D-finite sequence defined by the annihilating operator Sn - 1 and the initial conditions {0: 3}
        sage: D2(7.5)
        Univariate D-finite function defined by the annihilating operator Dx and the coefficient sequence defined by n and {0: 15/2}
        
        #conversion of rational functions
        sage: D1((n-2)/((n+1)*(n+5)))
        Univariate D-finite Sequence defined by the annihilating operator (n^4 + 11*n^3 + 26*n^2 - 44*n - 120)*Sn - n^4 - 10*n^3 - 24*n^2 + 10*n + 25 and the initial conditions {0: -2/5, 3: 1/32}
        sage: D2((x^2+4)/(x-1))
        Univariate D-finite function defined by the annihilating operator (x^3 - x^2 + 4*x - 4)*Dx - x^2 + 2*x + 4 and the coefficient sequence defined by (-4*n - 12)*Sn^3 + (4*n + 12)*Sn^2 + (-n + 1)*Sn + n - 1 and {0: -4, 1: -4, 2: -5}
    
        #conversion of symbolic expressions
        sage: D1(harmonic_number(n))
        Univariate D-finite Sequence defined by the annihilating operator (n + 2)*Sn^2 + (-2*n - 3)*Sn + n + 1 and the initial conditions {0: 0, 1: 1}
        sage: D2(sin(x^2))
        Univariate D-finite function defined by the annihilating operator x*Dx^2 - Dx + 4*x^3 and the coefficient sequence defined by (n^8 + 9*n^7 + 21*n^6 - 21*n^5 - 126*n^4 - 84*n^3 + 104*n^2 + 96*n)*Sn^4 + 4*n^6 + 12*n^5 - 20*n^4 - 60*n^3 + 16*n^2 + 48*n and {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: -1/6}
        
        """
        n = self.ore_algebra().is_S()
        
        #conversion for D-finite functions:
        if isinstance(x,DFiniteFunction):
            return self._construct_dfinite(x,n)
    
        #conversion for lists:
        elif type(x) == list:
            return self._construct_list(x,n)

        #conversion for (symbolic) numbers
        elif x in QQ or x.is_constant():
            if n:
                Sn = self.ore_algebra().gen()
                return UnivariateDFiniteSequence(self,Sn-1,{0:x})
            else:
                Dy = self.ore_algebra().gen()
                return UnivariateDFiniteFunction(self,Dy,{0:x})

        #conversion for rational functions
        elif x in self.base_ring().fraction_field():
               return self._construct_rational(x,n)
        else:
        #conversion for symbolic expressions
            return self._construct_symbolic(x,n)

                
    def _construct_dfinite(self,x,n):
        """
        Convert a d-finite object ``x`` into this ring, possibly non-canonically
        
        This is possible if there is a coercion from the Ore algebra of the parent of ``x`` into the Ore algebra of ``self``.
        In the shift case, if ``x`` represents a sequence that is defined over ``NN`` then also the codomain of ``self``
        has to be ``NN``(can not convert sequence over codomain ``NN`` into sequence over codomain ``ZZ``)
        
        INPUT:
        
        - ``x`` -- a d-finite object
        
        - ``n`` -- in the shift case the generator of the Ore algebra over which ``self`` is defined, in the differential case ``False``
        
        OUTPUT:
        
        The D-finite object ``x`` but now with ``self`` as parent
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: D2 = DFiniteFunctionRing(A,NN)
            sage: n = A.base_ring().gen()
            sage: a1 = D1(n)
            sage: a2 = D2(n)
            sage: a1
            Univariate D-finite sequence defined by the annihilating operator n*Sn - n - 1 and the initial conditions {0: 0, 1: 1, -1: -1}
            sage: a2
            Univariate D-finite sequence defined by the annihilating operator n*Sn - n - 1 and the initial conditions {0: 0, 1: 1}
            sage: D2(a1)
            Univariate D-finite sequence defined by the annihilating operator n*Sn - n - 1 and the initial conditions {0: 0, 1: 1}
            #D1(a2) would not work since a2 is defined over ``NN`` but D1 has codomain ``ZZ``
            
        """
        if self._coerce_map_from_(x.parent()):
            if n:
                if self._codomain == ZZ and x.parent()._codomain == NN:
                    raise TypeError, "can not convert sequence over codomain NN into sequence over codomain ZZ"
                else:
                    return UnivariateDFiniteSequence(self,x.ann(),x.initial_conditions())
            else:
                return UnivariateDFiniteFunction(self,x.ann(),x.initial_conditions())
        else:
            raise TypeError, str(x) + " could not be converted - the underlying Ore Algebras don't match"

    def _construct_list(self,x,n):
        """
        Convert a list of data ``x`` into this ring, possibly non-canonically.
        
        This method may lead to problems when the D-finite object has singularities because these are not considered during
        the conversion. So in this case maybe not all sequence/power series term can be computed.
        
        INPUT:
        
        - ``x`` -- a list of rational numbers that are the first terms of a sequence or a power series
        
        - ``n`` -- in the shift case the generator of the Ore algebra over which ``self`` is defined, in the differential case ``False``
        
        OUTPUT:
        
        A D-finite object with initial values from the list ``x`` and an ore operator which annihilates this initial values
        
        EXAMPLES::
            
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A)
            sage: D1([0,1,1,2,3,5,8])
            Univariate D-finite sequence defined by the annihilating operator -Sn^2 + Sn + 1 and the initial conditions {0: 0, 1: 1}

            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: D2([1,-1,1,-1,1,-1])
            Univariate D-finite function defined by the annihilating operator (x + 1)*Dx + 1 and the coefficient sequence defined by (n + 1)*Sn + n + 1 and {0: 1}
            
        """
        try:
            ann = guess(x,self.ore_algebra())
        except:
            raise ValueError, "no relation found"
    
        if n:
            return UnivariateDFiniteSequence(self,ann,x)
        else:
            return UnivariateDFiniteFunction(self,ann,x)

    def _construct_rational(self,x,n):
        """
        Convert a rational function ``x`` into this ring, possibly non-canonically.
        Pols of ``x`` will be represented as ``None`` entries.
        
        - ``x`` -- a list of rational numbers that are the first terms of a sequence or a power series
        
        - ``n`` -- in the shift case the generator of the Ore algebra over which ``self`` is defined, in the differential case ``False``
        
        OUTPUT:
        
        A D-finite object that either represents the sequence (a_n) = x(n) or the rational function x(z).
        
        EXAMPLES::
        
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: D1(1/n)
            Univariate D-finite sequence defined by the annihilating operator (n^3 + 3*n^2 + 2*n)*Sn - n^3 - 2*n^2 and the initial conditions {0: None, 1: 1, -2: -1/2, -1: -1}

            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: x = B.base_ring().gen()
            sage: D2(1/(x+1))
            Univariate D-finite function defined by the annihilating operator (x + 1)*Dx + 1 and the coefficient sequence defined by (n + 1)*Sn + n + 1 and {0: 1}
            
        """
        x = self.base_ring().fraction_field()(x)

        if n:
                
            #getting the operator
            A = self.ore_algebra()
            N = self.base_ring().gen()
            Sn = A.gen()
            f = x.numerator()
            g = x.denominator()
            ann = A(g(n+1)*f(n)*Sn - g(n)*f(n+1))
                
            #getting the order of the operator
            ord = 1

            #initial values, singularities and pols of the new operator
            singularities_positive = ann.singularities()
            singularities_negative = set()
            if self._backward_calculation == True:
                singularities_negative = ann.singularities(True)

            initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
            if self._backward_calculation == True:
                pols = set(r for (r,m) in g.roots() if r in ZZ)
            else:
                pols = set(r for (r,m) in g.roots() if r in NN)
                    
            int_val = {n:x(n) if n not in pols else None for n in initial_val}
            for n in pols:
                if self._backward_calculation == True and n-1 not in int_val:
                    int_val.update({n-1:x(n-1)})
                    ann = A(N - (n - 2))*ann
                    if n < 2:
                        int_val.update({n-2: x(n-2) if n-2 not in pols else None})
                if n+1 not in int_val:
                    int_val.update({n+1:x(n+1)})
                    ann = A(N - n)*ann

            return UnivariateDFiniteSequence(self,ann,int_val)
                    
        else:
            y = self.ore_algebra().is_D()
            Dy = self.ore_algebra().gen()
            R = self.ore_algebra().base_ring().change_var('n')
            OreAlg = OreAlgebra(R,'Sn')
    
            ann = x.denominator()**2*(x*Dy - x.derivative())
            
            #getting the operator of the sequence
            s_ann = ann.to_S(OreAlg)
            ord = s_ann.order()
                    
            #initial values and singularities of the sequence operator
            singularities_positive = s_ann.singularities()

            initial_val = set(range(ord)).union(singularities_positive)
            int_val = {n:(x.derivative(n)(0)/factorial(n)) for n in initial_val}
            
            #getting the coefficient sequence
            seq = UnivariateDFiniteSequence(DFiniteFunctionRing(OreAlg,NN),s_ann, int_val)
                
            return UnivariateDFiniteFunction(self,ann,seq)
    
    def _construct_symbolic(self,exp,n):
        """
        Convert a symbolic expression ``exp`` into this ring, possibly non-canonically.
        
        In the shift case the symoblic expression can contain the following symbolic functions:
        ``harmonic_number(n)``, ``binomial(k,n)``, ``binomial(n,k)`` (where ``k`` is a fixed integer) and ``factorial(n)``.
        Of course all other functions that can be converted into a D-finite sequnces (such as rational functions) can appear.
        Additionally addition and multiplication of these functions and composition of these functions with linear functions are
        supported.
        
        In the differential case the symbolic expression can contain serveral symbolic functions, including most trigonometric functions, square root, 
        logarithm, airy functions, bessel functions, error functions,\dots (for a detailled list see the documentation of ``dfinite_symbolic.py``). Of
        course all other functions that can be converrted into a D-finite function (such as rational functions) can appear. Additionally addition and
        multiplication of these functions and compostion of these functions with rational functions are supported.
        with linear inner functions
        
        INPUT:
        
        - ``exp`` -- a symbolic expression, i.e. an element of the ``Symbolic Ring``
        
        - ``n`` -- in the shift case the generator of the Ore algebra over which ``self`` is defined, in the differential case ``False``
        
        OUTPUT:
        
        A D-finite object that either represents the sequence (a_n) = exp(n) or the rational function exp(z).
        
        EXAMPLES::
        
        #discrete case
        sage: A = OreAlgebra(QQ['n'],'Sn')
        sage: D1 = DFiniteFunctionRing(A)
        sage: n = A.base_ring().gen()
        sage: D1(harmonic_number(3*n)+factorial(n+2))
        Univariate D-finite sequence defined by the annihilating operator (n^16 + 67/3*n^15 + 5936/27*n^14 + 33283/27*n^13 + 1013105/243*n^12 + 1870715/243*n^11 + 3546899/2187*n^10 - 66518617/2187*n^9 - 180628876/2187*n^8 - 226514354/2187*n^7 - 100116151/2187*n^6 + 114231970/2187*n^5 + 71608148/729*n^4 + 151833176/2187*n^3 + 17590912/729*n^2 + 820736/243*n)*Sn^3 + (-n^17 - 88/3*n^16 - 10184/27*n^15 - 8366/3*n^14 - 3138239/243*n^13 - 9055051/243*n^12 - 122248799/2187*n^11 + 44576237/2187*n^10 + 219018448/729*n^9 + 1502181299/2187*n^8 + 1677490715/2187*n^7 + 555946693/2187*n^6 - 1037674682/2187*n^5 - 1649354188/2187*n^4 - 1095953512/2187*n^3 - 365691616/2187*n^2 - 16532608/729*n)*Sn^2 + (2*n^17 + 164/3*n^16 + 17893/27*n^15 + 41819/9*n^14 + 4959904/243*n^13 + 13437490/243*n^12 + 160425214/2187*n^11 - 4681640/81*n^10 - 342643310/729*n^9 - 2132064758/2187*n^8 - 2167806307/2187*n^7 - 486539521/2187*n^6 + 1578966196/2187*n^5 + 2186715992/2187*n^4 + 1355369360/2187*n^3 + 427073584/2187*n^2 + 18294208/729*n)*Sn - n^17 - 79/3*n^16 - 8312/27*n^15 - 56099/27*n^14 - 2121212/243*n^13 - 5395544/243*n^12 - 55012850/2187*n^11 + 78281144/2187*n^10 + 437393203/2187*n^9 + 810512335/2187*n^8 + 716829946/2187*n^7 + 30708979/2187*n^6 - 218507828/729*n^5 - 752186248/2187*n^4 - 45694336/243*n^3 - 4227952/81*n^2 - 469312/81*n and the initial conditions {0: 2, 1: 47/6, 2: 529/20, 3: 309529/2520, 4: 20044421/27720, 5: 1817410157/360360}
        
        #differential case
        sage: B = OreAlgebra(QQ['x'],'Dx')
        sage: D2 = DFiniteFunctionRing(B)
        sage: x = B.base_ring().gen()
        sage: D2(cos(1/(x+1)-1) + erf(x))
        Univariate D-finite function defined by the annihilating operator (x^10 + 8*x^9 + 49/2*x^8 + 31*x^7 - 11/2*x^6 - 68*x^5 - 357/4*x^4 - 52*x^3 - 10*x^2 + 3*x + 5/4)*Dx^4 + (2*x^11 + 16*x^10 + 53*x^9 + 88*x^8 + 38*x^7 - 164*x^6 - 823/2*x^5 - 450*x^4 - 453/2*x^3 - 5/2*x^2 + 47*x + 29/2)*Dx^3 + (12*x^10 + 84*x^9 + 198*x^8 + 78*x^7 - 479*x^6 - 986*x^5 - 1585/2*x^4 - 148*x^3 + 443/2*x^2 + 175*x + 173/4)*Dx^2 + (12*x^9 + 72*x^8 + 116*x^7 - 100*x^6 - 511*x^5 - 538*x^4 - 68*x^3 + 251*x^2 + 331/2*x + 29)*Dx and the coefficient sequence defined by (n^22 + 43*n^21 + 801*n^20 + 8081*n^19 + 40846*n^18 - 13944*n^17 - 1682070*n^16 - 11112518*n^15 - 25070299*n^14 + 89686499*n^13 + 818733669*n^12 + 2169110853*n^11 - 742389844*n^10 - 20220171638*n^9 - 50901435632*n^8 - 21956242576*n^7 + 142899320096*n^6 + 308259971040*n^5 + 180792623232*n^4 - 163324131840*n^3 - 272840140800*n^2 - 105007104000*n)*Sn^6 + (4*n^22 + 166*n^21 + 2974*n^20 + 28542*n^19 + 130886*n^18 - 171372*n^17 - 6231176*n^16 - 36575164*n^15 - 64605776*n^14 + 373460638*n^13 + 2689186238*n^12 + 6033793702*n^11 - 5698412042*n^10 - 65356280184*n^9 - 142043584724*n^8 - 26346348520*n^7 + 449515069328*n^6 + 847568536352*n^5 + 421787311488*n^4 - 495654428160*n^3 - 726178867200*n^2 - 266582016000*n)*Sn^5 + (6*n^22 + 242*n^21 + 4195*n^20 + 38470*n^19 + 159371*n^18 - 383952*n^17 - 8732048*n^16 - 45754744*n^15 - 57488012*n^14 + 565391130*n^13 + 3343717267*n^12 + 6176999806*n^11 - 10861440253*n^10 - 79641213292*n^9 - 148020686630*n^8 + 15311579060*n^7 + 531755741688*n^6 + 877871220272*n^5 + 354977274816*n^4 - 564704001792*n^3 - 731128550400*n^2 - 255533875200*n)*Sn^4 + (4*n^22 + 162*n^21 + 2810*n^20 + 25614*n^19 + 103066*n^18 - 289884*n^17 - 5918028*n^16 - 29673956*n^15 - 30355744*n^14 + 395195762*n^13 + 2152208858*n^12 + 3562320414*n^11 - 8127784846*n^10 - 50596237720*n^9 - 86410512712*n^8 + 23694100024*n^7 + 332438952720*n^6 + 512279760480*n^5 + 180640020672*n^4 - 346400983296*n^3 - 420656716800*n^2 - 142904217600*n)*Sn^3 + (n^22 + 49*n^21 + 997*n^20 + 10625*n^19 + 54704*n^18 - 32072*n^17 - 2375566*n^16 - 14654418*n^15 - 26048219*n^14 + 152830341*n^13 + 1066265925*n^12 + 2210997433*n^11 - 2907141398*n^10 - 25551915982*n^9 - 49543388060*n^8 + 2387695768*n^7 + 171724256512*n^6 + 284507018464*n^5 + 112546512704*n^4 - 183544545408*n^3 - 232858137600*n^2 - 80147404800*n)*Sn^2 + (8*n^21 + 276*n^20 + 3932*n^19 + 26508*n^18 + 30380*n^17 - 882376*n^16 - 6740328*n^15 - 15149272*n^14 + 61917744*n^13 + 496511444*n^12 + 1034000604*n^11 - 1526644340*n^10 - 11950813220*n^9 - 20176853024*n^8 + 8536541488*n^7 + 78408071104*n^6 + 102984282688*n^5 + 17022151680*n^4 - 79682685696*n^3 - 74207232000*n^2 - 20976537600*n)*Sn + 2*n^21 + 68*n^20 + 946*n^19 + 6032*n^18 + 2720*n^17 - 233528*n^16 - 1558084*n^15 - 2442552*n^14 + 19458682*n^13 + 113389980*n^12 + 148923410*n^11 - 610084312*n^10 - 2562935452*n^9 - 2317160168*n^8 + 5511348928*n^7 + 14800820032*n^6 + 9062090048*n^5 - 7680884352*n^4 - 12177331200*n^3 - 4303411200*n^2 and {0: 1, 1: 2/sqrt(pi), 2: -1/2, 3: -2/3/sqrt(pi) + 1, 4: -35/24, 5: 1/5/sqrt(pi) + 11/6, 6: -1501/720, 7: -1/21/sqrt(pi) + 87/40, 8: -16699/8064, 9: 1/108/sqrt(pi) + 8791/5040, 10: -4260601/3628800, 11: -1/660/sqrt(pi) + 125929/362880}
        sage: D2(sinh_integral(x+1)*exp(3*x^2))
        Univariate D-finite function defined by the annihilating operator (x + 1)*Dx^3 + (-18*x^2 - 18*x + 2)*Dx^2 + (108*x^3 + 108*x^2 - 43*x - 19)*Dx - 216*x^4 - 216*x^3 + 186*x^2 + 114*x - 12 and the coefficient sequence defined by (n^13 + 43*n^12 + 797*n^11 + 8255*n^10 + 51363*n^9 + 187089*n^8 + 313151*n^7 - 264475*n^6 - 2183264*n^5 - 3322832*n^4 - 298848*n^3 + 3391920*n^2 + 2116800*n)*Sn^7 + (n^13 + 42*n^12 + 761*n^11 + 7710*n^10 + 46923*n^9 + 166806*n^8 + 268043*n^7 - 261870*n^6 - 1937024*n^5 - 2863248*n^4 - 193104*n^3 + 2950560*n^2 + 1814400*n)*Sn^6 + (-18*n^12 - 631*n^11 - 9300*n^10 - 73715*n^9 - 326844*n^8 - 696633*n^7 + 121860*n^6 + 3938215*n^5 + 7051062*n^4 + 1419164*n^3 - 6836760*n^2 - 4586400*n)*Sn^5 + (-18*n^12 - 619*n^11 - 8945*n^10 - 69460*n^9 - 301044*n^8 - 620487*n^7 + 167115*n^6 + 3605710*n^5 + 6252812*n^4 + 1116856*n^3 - 6109920*n^2 - 4032000*n)*Sn^4 + (108*n^11 + 3138*n^10 + 36870*n^9 + 218520*n^8 + 625464*n^7 + 319914*n^6 - 2807010*n^5 - 6455220*n^4 - 2270472*n^3 + 5913648*n^2 + 4415040*n)*Sn^3 + (108*n^11 + 3102*n^10 + 35970*n^9 + 209880*n^8 + 587664*n^7 + 264726*n^6 - 2689830*n^5 - 5994780*n^4 - 1986072*n^3 + 5517072*n^2 + 4052160*n)*Sn^2 + (-216*n^10 - 5400*n^9 - 51840*n^8 - 226800*n^7 - 331128*n^6 + 703080*n^5 + 2762640*n^4 + 1706400*n^3 - 2379456*n^2 - 2177280*n)*Sn - 216*n^10 - 5400*n^9 - 51840*n^8 - 226800*n^7 - 331128*n^6 + 703080*n^5 + 2762640*n^4 + 1706400*n^3 - 2379456*n^2 - 2177280*n and {0: sinh_integral(1), 1: sinh(1), 2: 1/2*cosh(1) - 1/2*sinh(1) + 3*sinh_integral(1), 3: -1/3*cosh(1) + 7/2*sinh(1), 4: 43/24*cosh(1) - 15/8*sinh(1) + 9/2*sinh_integral(1), 5: -37/30*cosh(1) + 757/120*sinh(1), 6: 797/240*cosh(1) - 523/144*sinh(1) + 9/2*sinh_integral(1), 7: -663/280*cosh(1) + 39793/5040*sinh(1), 8: 173251/40320*cosh(1) - 28231/5760*sinh(1) + 27/8*sinh_integral(1), 9: -144433/45360*cosh(1) + 316321/40320*sinh(1)}

        """
        R = self.base_ring()
    
        try:
            operator = exp.operator()
        except:
            raise TypeError, "no operator in this symbolic expression"

        operands = exp.operands()
        
        #add, mul
        if operator == add_vararg or operator == mul_vararg:
            while len(operands) > 1:
                operands.append( operator(self(operands.pop()), self(operands.pop())) )
            return operands[0]
        
       #pow
        elif operator == pow:
            exponent = operands[1]
            #pow
            if exponent in ZZ and exponent >= 0:
                return operator(self(operands[0]),ZZ(operands[1]))
            
            #sqrt - only works for sqrt(u*x+v) (linear inner function) - not implemented for sequences
            elif (not n) and (exponent - QQ(0.5) in ZZ) and (exponent >= 0):
                if R(operands[0]).degree() > 1:
                   raise ValueError, "Sqrt implemented only for linear inner function"
                ann = symbolic_database(self.ore_algebra(),operator,n,operands[0])
                ord = ann.order()
                int_val = range(ord)
                initial_val = {i: operator(operands[0],QQ(0.5)).derivative(i)(x = 0)/factorial(i) for i in int_val}
                f = UnivariateDFiniteFunction(self,ann,initial_val)
                return operator(f,2*exponent)
            else:
                raise ValueError, str(exponent) + " is not a suitable exponent"

        #call
        else:
            if len(operands) == 1:
                inner = operands[0]
                k = None
            else:
                if operands[0] in QQ:
                    k = operands[0]
                    inner = operands[1]
                elif operands[1] in QQ:
                    k = operands[1]
                    inner = operands[0]
                #special case - binomial coefficient with linear functions in n
                elif operator == binomial:
                    if operands[0].derivative() not in QQ or operands[1].derivative() not in QQ:
                        raise TypeError, "binomial coefficient only implemented for linear functions"
                    ann = symbolic_database(self.ore_algebra(),operator,R(operands[0]),R(operands[1]))
                    ord = ann.order()
                    singularities_positive = ann.singularities()
                    singularities_negative = set()
                    if self._backward_calculation == True:
                        singularities_negative = ann.singularities(True)
                    int_val = set(range(ord)).union(singularities_positive, singularities_negative)
                    initial_val = {i: exp(n = i) for i in int_val}
                    return UnivariateDFiniteSequence(self,ann,initial_val)
                else:
                    raise ValueError, "one of the operands has to be in QQ"
                    
            #sequences
            if n:
                inner = R(inner)
                
                #check if inner is of the form u*n + v
                if inner.derivative() in QQ:
                    ann = symbolic_database(self.ore_algebra(),operator,n,k)
                    ord = ann.order()
                    singularities_positive = ann.singularities()
                    singularities_negative = set()
                    if self._backward_calculation == True:
                        singularities_negative = ann.singularities(True)
                    int_val = set(range(ord)).union(singularities_positive, singularities_negative)
                    initial_val = {i: exp.subs(inner == var('n'))(n = i) for i in int_val}
                    #if inner == n we are done
                    if inner == n:
                        return UnivariateDFiniteSequence(self,ann,initial_val)
                    #otherwise we need composition
                    else:
                        return UnivariateDFiniteSequence(self,ann,initial_val)(inner)
                else:
                    raise TypeError, "inner argument has to be of the form u*x + v, with u,v rational"
            #functions
            else:
                x = R.gen()
                #check if inner is of the form u*x + v
                if inner.derivative() in QQ:
                    ann = symbolic_database(self.ore_algebra(),operator,inner,k)
                    ord = ann.order()
                    s_ann = ann.to_S(OreAlgebra(R.change_var('n'),"Sn"))
                    int_val = set(range(ord)).union(s_ann.singularities())
                    initial_val = {i: exp.derivative(i)(x = 0)/factorial(i) for i in int_val}
                    return UnivariateDFiniteFunction(self,ann,initial_val)
                else:
                    if len(operands) == 1:
                        return self(operator(x))(self(inner))
                    else:
                        return self(operator(k,x))(self(inner))
    
#testing and information retrieving

    def __eq__(self,right):
        """
        Tests if the two DFiniteFunctionRings ``self``and ``right`` are equal. 
        This is the case if and only if they are defined over equal Ore algebras and have the same codomain
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: D2 = DFiniteFunctionRing(A,NN)
            sage: D3 = DFiniteFunctionRing(A,ZZ)
            sage: D1 == D2
            False
            sage: D1 == D3
            True
        
        """
        try:
            return (self.ore_algebra() == right.ore_algebra() and self.codomain() == right.codomain())
        except:
            return False

    def is_integral_domain(self, proof = True):
        """
        Returns whether ``self`` is an integral domain.
        In the discrete case this is False; in the differential case this is true.
        """
        if self.ore_algebra().is_S():
            return False
        elif self.ore_algebra().is_D():
            return True
        else:
            raise NotImplementedError

    def is_noetherian(self):
        """
        """
        raise NotImplementedError
    
    def is_commutative(self):
        """
        Returns whether ``self`` is commutative.
        This is true for the function ring as well as the sequence ring
        """
        return True
            
    def construction(self):
        """
        """
        raise NotImplementedError

    def _coerce_map_from_(self, P):
        """
        If `P` is a DFiniteFunctionRing, then a coercion from `P` to ``self`` is possible if there is a
        coercion from the Ore algebra of `P` to the Ore algebra of ``self``. If `P`is not a DFiniteFunctionRing,
        then it is sufficient to have a coercion from `P` itself to the Ore algebra from ``self``.
        """
        if isinstance(P,DFiniteFunctionRing):
            return self._ore_algebra._coerce_map_from_(P.ore_algebra())
        return self._ore_algebra._coerce_map_from_(P)

    def _sage_input_(self, sib, coerced):
        r"""
        Produce an expression which will reproduce ``self`` when
        evaluated.
        """
        if self.codomain() == ZZ:
            return sib.name('DFiniteFunctionRing')(sib(self.ore_algebra()),sib(self.codomain()))
        else:
            return sib.name('DFiniteFunctionRing')(sib(self.ore_algebra()),sib.name('NN'))

    def _is_valid_homomorphism_(self, codomain, im_gens):
        """
        """
        raise NotImplementedError

    def __hash__(self):
        """
        """
        # should be faster than just relying on the string representation
        try:
            return self._cached_hash
        except AttributeError:
            pass
        h = self._cached_hash = hash((self.base_ring(),self.base_ring().variable_name()))
        return h

    def _repr_(self):
        """
        """
        try:
            return self._cached_repr
        except AttributeError:
            pass
        if self.ore_algebra().is_S():
            r = "Ring of D-finite sequences over "
        else:
            r = "Ring of D-finite functions over "
        r = r + self._base_ring._repr_()
        return r

    def _latex_(self):
        """
        """
        return "\mathcal{D}(" + self._ore_algebra._latex_() + ")"

    def base_ring(self):
        """
        Return the base ring over which the Ore algebra of the DFiniteFunctionRing is defined
        """
        return self._base_ring

    def ore_algebra(self):
        """
        Return the Ore algebra over which the DFiniteFunctionRing is defined
        """
        return self._ore_algebra

    def codomain(self):
        """
        Return the codomain over which the DFiniteFunctionRing is defined
        """
        return self._codomain

    def characteristic(self):
        """
        Return the characteristic of this DFiniteFunctionRing, which is the
        same as that of its base ring.
        """
        return self._base_ring.characteristic()

    def is_finite(self):
        """
        Return False since DFiniteFunctionRings are not finite (unless the base
        ring is 0.)
        """
        R = self._base_ring
        if R.is_finite() and R.order() == 1:
            return True
        return False

    def is_exact(self):
        """
        Return True if the Ore algebra over which the DFiniteFunctionRing is defined is exact
        """
        return self.ore_algebra().is_exact()

    def is_field(self, proof = True):
        """
        A DFiniteFunctionRing is not a field
        """
        return False
        
    def random_element(self, degree=2, *args, **kwds):
        r"""
        Return a random D-finite object.
        
        INPUT:
        
        -``degree`` (default 2) -- the degree of the ore operator of the random D-finite object
            
        OUTPUT:
        
        A D-finite sequence/function with a random ore operator of degree ``degree`` and random initial values constisting 
        of integers between -100 and 100.
        
        EXAMPLES::
        
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: D1.random_element()
            Univariate D-finite sequence defined by the annihilating operator (-n^2 + n)*Sn^2 + (22/9*n - 1/622)*Sn - 5/6*n^2 - n - 1 and the initial conditions {0: -88, 1: 18, 2: -49, 3: -67}
        
            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: D2.random_element(3)
            Univariate D-finite function defined by the annihilating operator 20*x*Dx^3 + (2/31*x^2 + 1/2*x + 1/2)*Dx^2 + (2*x^2 - 2*x + 1)*Dx + x^2 - 1/6 and the coefficient sequence defined by (20*n^3 + 361/2*n^2 + 1047/2*n + 486)*Sn^4 + (1/2*n^2 + 7/2*n + 6)*Sn^3 + (2/31*n^2 - 56/31*n - 751/186)*Sn^2 + (2*n + 2)*Sn + 1 and {0: -53, 1: 69, 2: -90, 3: -86}
            
        """
        #getting the operator
        ann = self.ore_algebra().random_element(degree)
        
        #initial values and singularities
        singularities_positive = ann.singularities()
        singularities_negative = set()
        if self._backward_calculation == True:
            singularities_negative = ann.singularities(True)
        
        initial_val = set(range(degree)).union(singularities_positive, singularities_negative)
        int_val = {n:randint(-100, 100) for n in initial_val}
        
        if self.ore_algebra().is_S():
            return UnivariateDFiniteSequence(self,ann,int_val)
        else:
            return UnivariateDFiniteFunction(self,ann,int_val)

    def _an_element_(self, *args, **kwds):
        """
        """
        return self.random_element()

#changing

    def change_base_ring(self,R):
        """
        Return a copy of ``self`` but with the base ring `R`
        """
        if R is self._base_ring:
            return self
        else:
            D = DFiniteFunctionRing(self._ore_algebra.change_ring(R), self._codomain)
            return D

    def change_codomain(self,R):
        """
        Return a copy of ``self``but with the codomain `R`
        """
        if R != NN and R != ZZ:
            raise TypeError, "Codomain not supported"

        if self.codomain() == R:
            return self

        return DFiniteFunctionRing(self.ore_algebra(), R)


####################################################################################################


class DFiniteFunction(RingElement):
    """
    An abstract class representing objects depending on one or more differential and one or more discrete variables
    defined by an annihilating holonomic system and a suitable set of initial conditions. 
    """

#constructor

    def __init__(self, parent, ann, initial_val, is_gen = False, construct=False, cache=True):
        """
        Constructor for D-finite sequences and functions
        
        INPUT:
        
        - ``parent`` -- a DFiniteFunctionRing
        
        - ``ann`` -- the operator in the corresponding Ore algebra annihilating the sequence or function
        
        - ``initial_val`` -- a list of initial values, determining the sequence or function, containing at least
          as many values as the order of ``ann`` predicts. For sequences these are the first sequence terms; for functions
          the first taylor coefficients. If the annhilating operator has singularities then ``initial_val`` has to be given
          in form of a dictionary containing the intial values and the singularities. For functions ``initial_val`` can also
          be a D-finite sequence representing the coefficient sequence of the function
          
                             
        OUTPUT:
        
        Either a D-finite sequence determined by ``ann`` and its initial conditions, i.e. initial values plus possible singularities
        or a D-finite function determined by ``ann`` and the D-finite sequence of its coefficients.
        
        For examples see the constructors of ``UnivariateDFiniteSequence`` and ``UnivariateDFiniteFunction`` respectively.
                            
        """
        RingElement.__init__(self, parent)
        self._is_gen = is_gen
    
        self.__ann = parent._ore_algebra(ann)
        ord = self.__ann.order()
        singularities = self.__ann.singularities()
        if parent._backward_calculation == True:
            singularities.update([a for a in self.__ann.singularities(True) if a < self.__ann.order()])
        
        #converting the initial values into sage rationals if possible
        if type(initial_val) == dict:
            initial_val = {key: QQ(initial_val[key]) if initial_val[key] in QQ else initial_val[key] for key in initial_val}
        elif type(initial_val) == list:
            initial_val = [QQ(k) if k in QQ else k for k in initial_val]
        
        
        initial_conditions = set(range(ord)).union(singularities)
    
        if parent.ore_algebra().is_S():
            #lists can only be given for sequences WITHOUT singularities (then the lists contains just the initial values)
            if type(initial_val) == list:
                self._initial_values = {i:initial_val[i] for i in range(min(ord,len(initial_val)))}
            else:
                if self.parent()._backward_calculation == False:
                    self._initial_values = {keys: initial_val[keys] for keys in initial_val if keys >= 0}
                else:
                    self._initial_values = initial_val
            
            if len(self._initial_values) < len(initial_conditions):
                if parent._backward_calculation is True:
                    print "Not enough initial values"
                
                #sequence comes from a d-finite function
                if parent._backward_calculation is False:
                    diff = len(initial_conditions) - len(self._initial_values)
                    zeros = {i:0 for i in range(-diff,0)}
                    self._initial_values.update(zeros)
                
                
        elif parent.ore_algebra().is_D():
            if isinstance(initial_val,UnivariateDFiniteSequence):
                self._initial_values = initial_val
            
            else:
                if len(initial_val) < ord:
                    raise ValueError, "not enough initial conditions given"
                R = parent.ore_algebra().base_ring().change_var('n')
                A = OreAlgebra(R,'Sn')
                D = DFiniteFunctionRing(A,NN)
                ann = self.__ann.to_S(A)
                self._initial_values = UnivariateDFiniteSequence(D, ann, initial_val)
        
        else:
            raise ValueError, "not a suitable D-finite function ring"

    
    def __copy__(self):
        """
        Return a "copy" of ``self``. This is just ``self``, since D-finite functions are immutable.
        """
        return self

# action

    def compress(self):
        """
        Tries to compress the D-finite object ``self`` as much as
        possible by trying to find a smaller annihilating operator and deleting
        redundant initial conditions.
        
        OUTPUT:
        
        A D-finite object which is equal to ``self`` but may consist of a smaller operator
        (in terms of the order) and less initial conditions. In the worst case if no
        compression is possible ``self`` is returned.
        
        EXAMPLES::
            
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A)
            sage: UnivariateDFiniteSequence(D1,"((n-3)*(n-5))*(Sn^2 - Sn - 1)",{0:0,1:1,5:5,7:13})
            Univariate D-finite sequence defined by the annihilating operator (n^2 - 8*n + 15)*Sn^2 + (-n^2 + 8*n - 15)*Sn - n^2 + 8*n - 15 and the initial conditions {0: 0, 1: 1, 5: 5, 7: 13}
            sage: _.compress()
            Univariate D-finite sequence defined by the annihilating operator -Sn^2 + Sn + 1 and the initial conditions {0: 0, 1: 1}
            
            sage: B = OreAlgebra(QQ[x],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: D2(sin(x)^2*cos(x)^2)
            Univariate D-finite function defined by the annihilating operator Dx^5 + 20*Dx^3 + 64*Dx and the coefficient sequence defined by (n^14 + 10*n^13 + 5*n^12 - 250*n^11 - 753*n^10 + 1230*n^9 + 8015*n^8 + 5450*n^7 - 21572*n^6 - 35240*n^5 + 480*n^4 + 28800*n^3 + 13824*n^2)*Sn^4 + (20*n^12 + 60*n^11 - 560*n^10 - 1800*n^9 + 4260*n^8 + 16380*n^7 - 5480*n^6 - 49200*n^5 - 21280*n^4 + 34560*n^3 + 23040*n^2)*Sn^2 + 64*n^10 - 1920*n^8 + 17472*n^6 - 52480*n^4 + 36864*n^2 and {0: 0, 1: 0, 2: 1, 3: 0, 4: -4/3, 5: 0, 6: 32/45, 7: 0, 8: -64/315}
            sage: _.compress()
            Univariate D-finite function defined by the annihilating operator Dx^3 + 16*Dx and the coefficient sequence defined by (n^3 + 3*n^2 + 2*n)*Sn^2 + 16*n and {0: 0, 1: 0, 2: 1}

        """
        A = self.parent().ore_algebra()
        d = self.__ann.degree()
        r = self.__ann.order()
        ini = copy(self.initial_conditions())
        
        if A.is_S():
            n = A.base_ring().gen()
        
            #special case r = 0, here we only compute the squarefree part of the operator
            if r == 0:
                return self.reduce_factors()
            
            #if the initial values contain symbolic expressions we can't use guessing - but we can
            #try to get rid of multiple common factors in the coefficients and redundant initial conditions
            elif not all(x in QQ for x in ini.values() if x != None):
                return self.reduce_factors()
            
            #if all initial conditions are in QQ we can try to guess a smaller operator
            else:
                #computing the data needed for guessing
                data = self.expand((r+1)*(d+2)+max(50,(r+1)*(d+2)))
                ann = guess(data,A,cut=None)
                
                #we did not find a better operator
                if ann.order() > r:
                    return self.reduce_factors()
            
                #order and minimal degree
                ord = ann.order()
                min_degree = next((index for index, coeff in enumerate(ann.list()) if coeff != 0), None)
        
                #checking if the singularities for forward calculation are really needed
                singularities_old = self.singularities()
                singularities_new = ann.singularities()
                singularities_missing = set([x for x in singularities_old.symmetric_difference(singularities_new) if x > max(0,ord-1)]).union(range(ord,r))
                
                if 0 in singularities_missing:
                    singularities_missing.remove(0)
            
                while len(singularities_missing) > 0:
                    k = min(singularities_missing)
                    
                    #taking care about NONE entries
                    if self[k] == None:
                        for l in range(k,k+ord+1):
                            ann = A(n - (l - ord))*ann
                            ini.update({l: self[l]})
                            
                            if self.parent()._backward_calculation == True and l < ord - min_degree:
                                ini.update({l-ord+min_degree: self[l-ord+min_degree]})
                            singularities_missing.remove(l)
                
                    #normal entries
                    else:
                        if self[k] == ann.to_list(self.expand(k-1)[k-ord:],ord+1,k-ord)[ord]:
                            if self.parent()._backward_calculation == True and k < ord - min_degree:
                                if self[k-ord+min_degree] == ann.to_list(self.expand(k-ord+min_degree-1)[k-ord+min_degree - ord:],ord+1,k-ord+min_degree - ord)[ord]:
                                    ini.pop(k)
                                    ini.pop(k-ord+min_degree)
                            else:
                                ini.pop(k)
                        else:
                            ann = A(n - (k - ord))*ann
                            ini.update({k: self[k]})
                            if self.parent()._backward_calculation == True and k < ord - min_degree:
                                ini.update({k-ord+min_degree: self[k-ord+min_degree]})
                        singularities_missing.remove(k)
                
                #checking if the singularities for backward calculation are really needed
                if self.parent()._backward_calculation == True:
                    singularities_old = self.singularities(True)
                    singularities_new = ann.singularities(True)
                    singularities_missing = set([x for x in singularities_old.symmetric_difference(singularities_new) if x < 0])
                    
                    #computing the operator for backward calculation
                    start = self.expand(ord-1)
                    start.reverse()
                    start.pop()
                    while len(singularities_missing) > 0:
                        k = max(singularities_missing)
                        #taking care about NONE entries
                        if self[k] == None:
                            for l in xrange(k-ord,k+1):
                                ann = A(n - (l - min_degree))*ann
                                ini.update({l: self[l]})
                                if l >= min_degree:
                                    ini.update({l-min_degree+ord: self[l-min_degree+ord]})
                                singularities_missing.remove(l)
                        #normal entries
                        else:
                            ann_backwards = ann.annihilator_of_composition((ord-1)-n)
                            if self[k] == ann_backwards.to_list(start + self.expand(k+1),ord-k)[ord-k-1]:
                                if k >= min_degree:
                                    if self[k-min_degree+ord] == ann_backwards.to_list(start + self.expand(k-min_degree+ord),-k-min_degree)[-k-min_degree-1]:
                                        ini.pop(k)
                                        ini.pop(k-min_degree+ord)
                                else:
                                    ini.pop(k)
                            else:
                                ann = A(n - (k - min_degree))*ann
                                ini.update({k: self[k]})
                            singularities_missing.remove(k)

                result = UnivariateDFiniteSequence(self.parent(),ann,ini)
                
                if self == result:
                    return result
                else:
                    return self.reduce_factors()
        
        else:
            #compress the coefficient sequence
            seq = ini.compress()
            
            #try to guess a smaller differential operator
            if all(x in QQ for x in ini.initial_conditions().values()):
                data = self.expand((r+1)*(d+2)+max(50,(r+1)*(d+2)))
                ann = guess(data,A,cut=None)
                
                #no better operator found
                if ann.order() > r:
                    ann = self.__ann
            else:
                ann = self.__ann
           
            result = UnivariateDFiniteFunction(self.parent(),ann,seq)
            
            if self == result:
                return result
            else:
                return UnivariateDFiniteFunction(self.parent(),self.__ann,seq)
                
                
    def reduce_factors(self):
        """
        Tries to delete factors of order 0 of the annihilating operator of ``self`` which appear more than
        once. Additionally this method tries to delete redundant initial conditions. This method is a subroutine
        of compress
        
        OUTPUT:
        
        A D-finite object which is equal to ``self`` but may consist of a smaller operator
        (in terms of the degree) and less initial conditions. In the worst case if no
        reduction is possible ``self`` is returned.
        
        EXAMPLES::
        
        sage: A = OreAlgebra(QQ['n'],'Sn')
        sage: D1 = DFiniteFunctionRing(A)
        sage: UnivariateDFiniteSequence(D1,"((n-3)*(n-5))*(Sn^2 - Sn - 1)",{0:0,1:1,5:5,7:13})
        Univariate D-finite sequence defined by the annihilating operator (n^2 - 8*n + 15)*Sn^2 + (-n^2 + 8*n - 15)*Sn - n^2 + 8*n - 15 and the initial conditions {0: 0, 1: 1, 5: 5, 7: 13}
        sage: _.reduce_factors()
        Univariate D-finite sequence defined by the annihilating operator -Sn^2 + Sn + 1 and the initial conditions {0: 0, 1: 1}
            
        sage: B = OreAlgebra(QQ[x],'Dx')
        sage: D2 = DFiniteFunctionRing(B)
        sage: D2(sin(x)^2*cos(x)^2)
        Univariate D-finite function defined by the annihilating operator Dx^5 + 20*Dx^3 + 64*Dx and the coefficient sequence defined by (n^14 + 10*n^13 + 5*n^12 - 250*n^11 - 753*n^10 + 1230*n^9 + 8015*n^8 + 5450*n^7 - 21572*n^6 - 35240*n^5 + 480*n^4 + 28800*n^3 + 13824*n^2)*Sn^4 + (20*n^12 + 60*n^11 - 560*n^10 - 1800*n^9 + 4260*n^8 + 16380*n^7 - 5480*n^6 - 49200*n^5 - 21280*n^4 + 34560*n^3 + 23040*n^2)*Sn^2 + 64*n^10 - 1920*n^8 + 17472*n^6 - 52480*n^4 + 36864*n^2 and {0: 0, 1: 0, 2: 1, 3: 0, 4: -4/3, 5: 0, 6: 32/45, 7: 0, 8: -64/315}
        sage: _.reduce_factors()
        Univariate D-finite function defined by the annihilating operator Dx^5 + 20*Dx^3 + 64*Dx and the coefficient sequence defined by (n^9 + 20*n^8 + 170*n^7 + 800*n^6 + 2273*n^5 + 3980*n^4 + 4180*n^3 + 2400*n^2 + 576*n)*Sn^4 + (20*n^7 + 260*n^6 + 1340*n^5 + 3500*n^4 + 4880*n^3 + 3440*n^2 + 960*n)*Sn^2 + 64*n^5 + 640*n^4 + 2240*n^3 + 3200*n^2 + 1536*n and {0: 0, 1: 0, 2: 1, 3: 0, 4: -4/3}
        
        """
        A = self.parent().ore_algebra()
        n = A.is_S()
        ini = copy(self.initial_conditions())
        ann = self.__ann
                
        #order and minimal degree
        ord = ann.order()
        min_degree = next((index for index, coeff in enumerate(ann.list()) if coeff != 0), None)
                
        #killing multiple common factors in coefficients
        g = gcd(ann.coefficients())
        g_fac = g.factor()
        g_roots = [r for (r,m) in g.roots()]
        multiple_factors = prod([factor for (factor,power) in g_fac if power > 1])
        ann = A([coeff/multiple_factors for coeff in ann.coefficients(sparse = False)])
                
        if n:
            #checking if all posiitive initial conditions are really needed
            singularities_pos = set([x+ord for x in g_roots if x+ord > max(0,ord-1)])
            while len(singularities_pos) > 0:
                k = min(singularities_pos)
                #taking care about NONE entries
                if self[k] == None:
                    for l in xrange(k,k+ord+1):
                        singularities_pos.remove(l)
                
                #normal entries
                else:
                    ann = A([coeff/(n - (k - ord)) for coeff in ann.coefficients(sparse = False)])
                    if self[k] == ann.to_list(self.expand(k-1)[k-ord:],ord+1,k-ord)[ord]:
                        if self.parent()._backward_calculation == True and k < ord - min_degree:
                            if self[k-ord+min_degree] == ann.to_list(self.expand(k-ord+min_degree-1)[k-ord+min_degree -ord:],ord+1,k-ord+min_degree-ord)[ord]:
                                ini.pop(k)
                                ini.pop(k-ord+min_degree)
                            else:
                                ann = A(n - (k - ord))*ann
                        else:
                            ini.pop(k)
                    else:
                        ann = A(n - (k - ord))*ann
                    singularities_pos.remove(k)
        
            #checking if all negative initial conditions are really needed
            if self.parent()._backward_calculation == True:
                start = self.expand(ord-1)
                start.reverse()
                start.pop()
                singularities_neg = set([x+min_degree for x in g_roots if x+min_degree < 0])
                while len(singularities_neg) > 0:
                    k = max(singularities_neg)
                    #taking care of None entries
                    if self[k] == None:
                        for l in range(k-ord,k+1):
                            singularities_neg.remove(l)
                    #normal entries
                    else:
                        ann = A([coeff/(n - (k - min_degree)) for coeff in ann.coefficients(sparse = False)])
                        ann_backwards = ann.annihilator_of_composition((ord-1)-n)
                        if self[k] == ann_backwards.to_list(start + self.expand(k+1),ord-k)[ord-k-1]:
                            if k >= min_degree:
                                if self[k-min_degree+ord] == ann_backwards.to_list(start + self.expand(k-min_degree+ord),-k-min_degree)[-k-min_degree-1]:
                                    ini.pop(k)
                                    ini.pop(k-min_degree+ord)
                                else:
                                    ann = A(n - (k - min_degree))*ann
                            else:
                                ini.pop(k)
                        else:
                            ann = A(n - (k - min_degree))*ann
                        singularities_neg.remove(k)
        
            result = UnivariateDFiniteSequence(self.parent(),ann,ini)
    
        else:
            result = UnivariateDFiniteFunction(self.parent(), ann, self.initial_conditions().reduce_factors())
        
        #checking if the result is indeed equal to the input
        if self == result:
            return result
        else:
            return self

    def __call__(self, *x, **kwds):
        """
        Lets ``self`` act on ``x`` and returns the result.
        ``x`` may be either a constant, then this computes an evaluation,
        or a (suitable) expression, then it represents composition and we return a new DFiniteFunction object.
        """
        raise NotImplementedError
    
    def singularities(self, backwards = False):
        """
        Returns the integer singularities of the annihilating operator of ``self``.
        
        INPUT:
        
        - ``backwards`` (default ``False``) -- boolean value that decides whether the singularities needed for the forward calculation
          are returned or those for backward calculation.
          
        OUTPUT:
        
        - If ``backwards`` is ``False``, a set containing the roots of the leading coefficient of the annihilator of ``self`` shifted by 
          its order is returned
        - If ``backwards`` is ``True``, a set containing the roots of the coefficient corresponding to the term of minimal order 
          (regarding `Sn` or `Dx` respectively) is returned; shifted by the order of this term
          
        EXAMPLES::
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D,"(n-3)*(n+2)*Sn^3 + n^2*Sn^2 - (n-1)*(n+5)*Sn", {0:0,1:1,2:2,6:1,-4:1})
            sage: a.singularities()
            {1, 6}
            sage: a.singularities(True)
            {-4, 2}
        """
        return self.__ann.singularities(backwards)
    
    def critical_points(self, order = None, backwards = False):
        """
        Returns the singularities of ``self`` and the values around those singularities that can be affected.
        
        INPUT:
        
        - ``order`` (default: the order of the annihilating operator of ``self``) -- nonnegative integer that determines how many values
          after or before each singularity are returned
        
        - ``backwards`` (default ``False``) -- boolean value that determines whether we are interested in the critial points for forward calculation, 
          i.e. the singularities of the leading coefficent and ``order`` many values after each singularity, or in those for backward calculation, i.e.
          the singularities of the coefficient of minimal degree (regarding `Sn` or `Dx`respectively) and ``order`` many values before each singularity.
        
        OUTPUT:
        
        A set containing the critical points for forward calculation (if ``backwards`` is False) or those for backward calculation.
        
        EXAMPLES::
        
        A = OreAlgebra(QQ['n'],'Sn')
        sage: D = DFiniteFunctionRing(A,ZZ)
        sage: a = UnivariateDFiniteSequence(D,"(n-3)*(n+2)*Sn^3 + n^2*Sn^2 - (n-1)*(n+5)*Sn", {0:0,1:1,2:2,6:1,-4:1})
        sage: a.critical_points()
        {1, 2, 3, 4, 6, 7, 8, 9}
        sage: a.critical_points(2,True)
        {-6, -5, -4, 0, 1, 2}
        
        """
        if order == None:
            ord = self.__ann.order()
        else:
            ord = order
        
        critical_points = set()
        
        if backwards == False:
            singularities_positive = self.__ann.singularities()
            for n in singularities_positive:
                critical_points.update(range(n,n+ord+1))
        
        elif self.parent()._backward_calculation == True:
            singularities_negative = self.__ann.singularities(True)
            for n in singularities_negative:
                critical_points.update(range(n-ord,n+1))
        
        return critical_points

#tests

    def __is_zero__(self):
        """
        Return whether ``self`` is the zero sequence 0,0,0,\dots or the zero function f(x) = 0 \forall x, respectively.
        This is the case iff all the initial conditions are 0 or ``None``.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: a = D1(0)
            sage: a.__is_zero__()
            True
            sage: a = D1.random_element()
            sage: a.__is_zero__()
            False
        
        """
        if self.parent().ore_algebra().is_S():
            for x in self.initial_conditions():
                if self[x] != 0 and self[x] != None:
                    return False
            return True
        else:
            return self.initial_conditions().__is_zero__()
    


    def __eq__(self,right):
        """
        Return whether the two DFiniteFunctions ``self`` and ``right`` are equal.
        More precicsely it is tested if the difference of ``self`` and ``right`` equals 0.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = D([0,1,1,2,3,5])
            sage: b = UnivariateDFiniteSequence(D,"Sn^2-Sn-1",[0,1])
            sage: a == b
            True
            
        """
        if self.parent() != right.parent():
            right = self.parent()(right)
        return (self.__add_without_compress__(-right)).__is_zero__()

    
    def __ne__(self,right):
        """
        Return ``True``if the DFiniteFunctions ``self`` and ``right`` are NOT equal; ``False`` otherwise
        
        """
        return not self.__eq__(right)

    def _is_atomic(self):
        """
        """
        raise NotImplementedError

    def is_unit(self):
        r"""
        Return ``True`` if ``self`` is a unit.
        This is the case if the annihialting operator of ``self`` has order 1. Otherwise we can not decide whether
        ``self``is a unit or not.
        
        """
        if self.__ann.order() == 1:
            return True
        raise NotImplementedError
       
    def is_gen(self):
        r"""
        Return ``False``; the parent ring is not finitely generated.
        """
        return False
    
    def prec(self):
        """
        Return the precision of this object. 
        """
        return Infinity
    
    def change_variable_name(self, var):
        """
        Return a copy of ``self`` but with an Ore operator in the variable ``var``
        
        INPUT:
        
        - ``var`` -- the new variable
        
        EXAMPLES::
        
            sage: A = OreAlgebra(ZZ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D, "Sn**2 - Sn - 1", [0,1])
            sage: c = a.change_variable_name('x')
            sage: a
            Univariate D-finite sequence defined by the annihilating operator Sn^2 - Sn - 1 and the initial conditions {0: 0, 1: 1}
            sage: c
            Univariate D-finite sequence defined by the annihilating operator x^2 - x - 1 and the initial conditions {0: 0, 1: 1}
        
        """
        D = DFiniteFunctionRing(self.parent().ore_algebra().change_var(var),self.parent()._codomain)
        if self.parent().ore_algebra().is_S():
            return UnivariateDFiniteSequence(D, self.__ann, self._initial_values)
        else:
            return UnivariateDFiniteFunction(D,self.__ann, self._initial_values)
        
    def change_ring(self, R):
        """
        Return a copy of ``self`` but with an annihilating operator of an Ore algebra over ``R``
        
        """
        D = self.parent().change_base_ring(R)
        if self.parent().ore_algebra().is_S():
            return UnivariateDFiniteSequence(D, self.__ann, self._initial_values)
        else:
            return UnivariateDFiniteFunction(D,self.__ann, self._initial_values)

    def __getitem__(self, n):
        """
        """
        raise NotImplementedError

    def __setitem__(self, n, value):
        """
        """
        raise IndexError("D-finite functions are immutable")

    def __iter__(self):
        return NotImplementedError

#conversion

    def __float__(self):
        """
        Tries to convert ``self`` into a float.
        This is possible iff ``self`` represents a constant sequence or constant function for some constant values in ``QQ``.
        If the conversion is not possible an error message is displayed.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: a = D1(3.4)
            sage: b = D2(4)
            sage: float(a)
            3.4
            sage: float(b)
            4.0
            
        """
        i = self._test_conversion_()
        if i != None:
            return float(i)
        
        raise TypeError, "no conversion possible"
    
    def __int__(self):
        """
        Tries to convert ``self`` into an integer.
        This is possible iff ``self`` represents a constant sequence or constant function for some constant value in ``ZZ``.
        If the conversion is not possible an error message is displayed.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: a = D1(3.4)
            sage: b = D2(4)
            sage: int(b)
            4
            #int(a) would lead to an error message

        """
        i = self._test_conversion_()
        if i != None and i in ZZ:
            return int(i)
        
        raise TypeError, "no conversion possible"

    def _integer_(self, ZZ):
        """
        Tries to convert ``self`` into a Sage integer.
        This is possible iff ``self`` represents a constant sequence or constant function for some constant value in ``ZZ``.
        If the conversion is not possible an error message is displayed.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: a = D1(3.4)
            sage: b = D2(4)
            sage: ZZ(b)
            4
            #ZZ(a) would lead to an error message

        """
        return ZZ(int(self))

    def _rational_(self):
        """
        Tries to convert ``self`` into a Sage rational.
        This is possible iff ``self`` represents a constant sequence or constant function for some constant value in ``QQ``.
        If the conversion is not possible an error message is displayed.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: a = D1(3.4)
            sage: b = D2(4)
            sage: QQ(a)
            17/5
            sage: QQ(b)
            4
            
        """
        i = self._test_conversion_()
        if i != None and i in QQ:
            return QQ(i)
        
        raise TypeError, "no conversion possible"
    
    def __long__(self):
        """
        Tries to convert ``self`` into a long integer.
        This is possible iff ``self`` represents a constant sequence or constant function for some constant value in ``ZZ``.
        If the conversion is not possible an error message is displayed.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: a = D1(3.4)
            sage: b = D2(4)
            sage: long(b)
            4L
            #long(a) would lead to an error message
            
        """
        i = self._test_conversion_()
        if i != None and i in ZZ:
            return long(i)

        raise TypeError, "no conversion possible"

    def _symbolic_(self, R):
        raise NotImplementedError

#representation

    def _repr(self, name=None):
        return self._repr_()

    def _repr_(self):
        """
        """
        r = "Univariate D-finite "
        if self.parent().ore_algebra().is_S():
            r = r + "sequence defined by the annihilating operator "
            r = r + str(self.__ann) + " and the initial conditions "
            r = r + str(self._initial_values)
        else:
            r = r + "function defined by the annihilating operator "
            r = r + str(self.__ann) + " and the coefficient sequence defined by "
            r = r + str(self.initial_conditions().__ann) + " and " + str(self.initial_conditions().initial_conditions())
            
        return r

    def _latex_(self, name=None):
        """
        """
        if self.parent().ore_algebra().is_S():
            r = '\\text{D-finite sequence defined by the annihilating operator }'
            r = r + latex(self.__ann) + '\\text{ and the initial conditions }'
            r = r + latex(self.initial_conditions())
        else:
            r = '\\text{D-finite function defined by the annihilating operator }'
            r = r + latex(self.__ann) + '\\text{ and the coefficent sequence defined by }'
            r = r + latex(self.initial_conditions().__ann) + '\\text{ and }' + latex(self.initial_conditions().initial_conditions())

        return r
        
    def _sage_input_(self, sib, coerced):
        r"""
        Produce an expression which will reproduce ``self`` when evaluated.
        
        """
        par = self.parent()
        int_cond = self.initial_conditions()
        if par.ore_algebra().is_S():
            init = sib({sib.int(a):sib.int(int_cond[a]) for a in int_cond})
            result = sib.name('UnivariateDFiniteSequence')(sib(par),sib(self.__ann),init)
        else:
            result = sib.name('UnivariateDFiniteFunction')(sib(par),sib(self.__ann),sib(int_cond))
        return result

    def dict(self):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError

# arithmetic

    def __invert__(self):
        """
        works if 1/self is again d-finite. 
        """
        return NotImplementedError

    def __div__(self, right):
        """
        This is division, not division with remainder. Works only if 1/right is d-finite. 
        """
        return self*right.__invert__()

    def __pow__(self, n, modulus = None):
        """
        """
        return self._pow(n)
        
    def _pow(self, n):
        """
        Return ``self`` to the n-th power
        
        INPUT:
        
        - ``n`` -- a non-negative integer
        
        OUTPUT:
        
        self^n
        
        EXAMPLES::
        
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D1(n)
            sage: a**3
            Univariate D-finite sequence defined by the annihilating operator (n^12 + 3*n^11 - 6*n^10 - 18*n^9 + 9*n^8 + 27*n^7 - 4*n^6 - 12*n^5)*Sn - n^12 - 6*n^11 - 6*n^10 + 26*n^9 + 60*n^8 + 6*n^7 - 86*n^6 - 66*n^5 + 21*n^4 + 40*n^3 + 12*n^2 and the initial conditions {0: 0, 1: 1, 2: 8, 3: 27, -2: -8, -3: -27, -1: -1}
            
            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: x = B.base_ring().gen()
            sage: b = D2(x^2)
            sage: b**2
            Univariate D-finite function defined by the annihilating operator x*Dx - 4 and the coefficient sequence defined by n^2 - 6*n + 8 and {2: 0, 4: 1}
            
        """
        if n == 0:
            return self.parent().one()
        if n == 1:
            return self
        
        #for small n the traditional method is faster
        if n <= 10:
            return self * (self._pow(n-1))

        #for larger n we use repeated squaring
        else:
            result = self.parent().one()
            bit = bin(n)[2:] #binary representation of n
            for i in range(len(bit)):
                result = result * result
                if bit[i] == '1':
                    result = result * self
            return result
                   
    def __floordiv__(self,right):
        """
        """
        raise NotImplementedError

    def __mod__(self, other):
        """
        """
        raise NotImplementedError

#base ring related functions
        
    def base_ring(self):
        """
        Return the base ring of the parent of ``self``.
        
        """
        return self.parent().base_ring()

#part extraction functions

    def ann(self):
        """
        Return the annihilating operator of ``self``
        """
        return self.__ann
    
    def initial_values(self):
        """
        Return the initial values of ``self`` in form of a list.
        
        In the discrete case those are the first `r` sequence terms, where `r` is the order of the annihilating
        operator of ``self``. In the differential case those are the first `r` coefficients of ``self``, where
        `r` is again the order of the annihilating operator of ``self``.
        Singularities that might be saved will not be considered, unless they are within the first `r` terms. To get all saved
        values (initial values plus singularities) use the method ``initial_conditions``
        
        EXAMPLES::
        
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D1, "(n+3)*(n-2)*Sn^2 + Sn + 4*n", {0:0,1:1,4:3,-1:2})
            sage: a.initial_values()
            [0, 1]
            
            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: b = UnivariateDFiniteFunction(D2, "(x-3)*Dx - 1", {0:-3})
            sage: b.initial_values()
            [-3]
    
        """
        if self.parent().ore_algebra().is_S():
            if self.parent()._backward_calculation is False and min(self.initial_conditions()) < 0:
                m = min(self.initial_conditions())
                result = [self._initial_values[key] for key in range(m,self.__ann.order()+m)]
            else:
                result = [self._initial_values[key] for key in range(self.__ann.order())]
            return result
        else:
             return self._initial_values.expand(self.__ann.order()-1)

    def initial_conditions(self):
        """
        Return all initial conditions of ``self``.
        
        In the discrete case the initial conditions are all values that are saved, i.e. the initial values and all singularities.
        In the differential case this method will return the coefficient sequence of ``self`` in form of a UnivariateDFiniteSequence object.
        To get all saved values of a UnivariateDFiniteFunction one has to call this method twice (see examples).
        
        EXAMPLES::
          
            #discrete case
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D1 = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D1, "(n+3)*(n-2)*Sn^2 + Sn + 4*n", {0:0,1:1,4:3,-1:2})
            sage: a.initial_conditions()
            {-1: 2, 0: 0, 1: 1, 4: 3}
            
            #differential case
            sage: B = OreAlgebra(QQ['x'],'Dx')
            sage: D2 = DFiniteFunctionRing(B)
            sage: b = UnivariateDFiniteFunction(D2, "(x-3)*Dx - 1", {0:-3})
            sage: b.initial_conditions()
            Univariate D-finite sequence defined by the annihilating operator (-3*n - 3)*Sn + n - 1 and the initial conditions {0: -3}
            sage: b.initial_conditions().initial_conditions()
            {0: -3}
                        
        """
        return self._initial_values

#############################################################################################################
    
class UnivariateDFiniteSequence(DFiniteFunction):
    """
    D-finite sequence in a single discrete variable.
    """
    
#constructor

    def __init__(self, parent, ann, initial_val, is_gen=False, construct=False, cache=True):
        """
        Constructor for a D-finite sequence in a single discrete variable.
        
        INPUT:
        
        - ``parent`` -- a DFiniteFunctionRing defined over an OreAlgebra with the shift operator
        
        - ``ann`` -- an annihilating operator, i.e. an element from the OreAlgebra over which the DFiniteFunctionRing is defined,
           that defines a differential equation for the function ``self`` should represent.
           
        - ``initial_val`` -- either a dictionary (or a list if no singularities occur) which contains the first r sequence terms (and all singularities if
          there are some) of ``self``, where r is the order of ``ann``
          
        OUTPUT:
        
        An object consisting of ``ann`` and a dictionary that represents the D-finite sequence which is annihilated by ``ann``, has the initial values that 
        appear in the dictionary and at all singularities of ``ann`` has the values that the dictionary predicts.
       
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: n = A.base_ring().gen()
            sage: Sn = A.gen()
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: UnivariateDFiniteSequence(D,Sn^2 - Sn - 1, [0,1])
            Univariate D-finite sequence defined by the annihilating operator Sn^2 - Sn - 1 and the initial conditions {0: 0, 1: 1}
            sage: UnivariateDFiniteSequence(D, (n^2 - n)*Sn - n^2 - n, {0: 0, 1: 0, 2: 2, -1: 2})
            Univariate D-finite sequence defined by the annihilating operator (n^2 - n)*Sn - n^2 - n and the initial conditions {0: 0, 1: 0, 2: 2, -1: 2}
            
        """
        if not parent.ore_algebra().is_S():
            raise TypeError, "Not the Shift Operator"
        super(UnivariateDFiniteSequence, self).__init__(parent, ann, initial_val, is_gen, construct, cache)

#action

    def __call__(self, x):
        """
        Lets ``self`` act on `x`.
        
        If `x` is an integer (or a float, which then gets ``cut`` to an integer) the x-th sequence term
        is returned. This is also possible for negative `x` if the DFiniteFunctionRing is defined
        over the codomain ZZ. If `x` is a suitable expression, i.e. of the form x = u*n + v for
        some u,v in QQ, it is interpreted as the composition self(floor(x(n)))
        
        EXAMPLES::
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = UnivariateDFiniteSequence(D, "Sn^2 - Sn - 1", [0,1]) #the Fibonacci numbers
            sage: a(-5)
            5
            sage: a(2*n+3).expand(10) #the odd Fibonacci numbers staring with a_3
            [2, 5, 13, 34, 89, 233, 610, 1597, 4181, 10946, 28657]

        """
        try:
            #x is a number
            n = int(x)
        except:
            #x is of the form u*n + v
            y = var('y')
            
            #getting the operator
            A = self.parent().ore_algebra()
            N = A.is_S()
            if isinstance(x,UnivariateDFiniteSequence):
                x = x.to_polynomial()
            else:
                x = QQ[N](x)
            ann = self.ann().annihilator_of_composition(x)
            
            #getting the largest and smallest degree of the new operator
            ord = ann.order()
            min_degree = next((index for index, coeff in enumerate(ann.list()) if coeff != 0), None)
            
            #initial values and singularities of the new operator
            singularities_positive = ann.singularities()
            singularities_negative = set()
            if self.parent()._backward_calculation == True:
                singularities_negative = ann.singularities(True)
        
            initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
            int_val = {n:self[floor(x(n))] for n in initial_val}
                
            #critical points for forward calculation
            critical_points_positive = set()
            for n in singularities_positive:
                critical_points_positive.update(range(n+1,n+ord+1))
            
            for n in self.critical_points(ord):
                k = ceil(solve( n == x(y), y)[0].rhs())
                if n == floor(x(k)):
                    critical_points_positive.update([k])
            
            for n in critical_points_positive:
                int_val.update({n:self[floor(x(n))]})
                ann = A(N - (n - ord) )*ann
                if self.parent()._backward_calculation == True and n < ord - min_degree:
                    int_val.update({(n-ord)+min_degree: self[floor(x(n-ord+min_degree))]})
                
            #critical points for backward calculation
            critical_points_negative = set()
            for n in singularities_negative:
                critical_points_negative.update(range(n-ord,n))
            
            for n in self.critical_points(ord,True):
                k = ceil(solve( n == x(y), y)[0].rhs())
                if n == floor(x(k)):
                    critical_points_negative.update([k])
            
            for n in critical_points_negative:
                    int_val.update({n:self[floor(x(n))]})
                    ann = A(N - (n - min_degree) )*ann                                     
                    if n >= min_degree:
                        int_val.update({(n-min_degree)+ord : self[floor(x(n-min_degree+ord))]})

            return UnivariateDFiniteSequence(self.parent(), ann, int_val)
            
        return self[n]

    def _test_conversion_(self):
        """
        Test whether a conversion of ``self`` into an int/float/long/... is possible;
        i.e. whether the sequence is constant or not.
        
        OUTPUT:
        
        If ``self`` is constant, i.e. there exists a `k` in QQ, such that self(n) = k for all n in NN,
        then this value `k` is returned. If ``self`` is not constant ``None`` is returned.
        
        EXAMPLES::
            
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D(3)
            sage: b = D(n)
            sage: a._test_conversion_()
            3
            sage: b._test_conversion_()
            #None is returend
            
        """
        ini = self.initial_values()
        if len(ini) > 0:
            i = self.initial_values()[0]
        else:
            i = 0
        if all(x == i for x in self.initial_values()):
            Sn = self.parent().ore_algebra().gen()
            if self.ann().quo_rem(Sn-1)[1].is_zero():
                return i
        return None
    
    def dict(self):
        """
        """
        raise NotImplementedError

    def list(self):
        """
        """
        raise NotImplementedError
    
    def to_polynomial(self):
        """
        Try to convert ``self`` into a polynomial.
        
        OUTPUT:
        
        Either a polynomial f(n) from the base ring of the OreAlgebra of the annihilating operator of ``self`` such that self(n) = f(n)
        for all n in NN or an error message if no such polynomial exists.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D(3*n^3 + 5*n - 10)
            sage: a.to_polynomial()
            3*n^3 + 5*n - 10
            sage: l = D(legendre_P(5,n))
            sage: l
            Univariate D-finite sequence defined by the annihilating operator (63/8*n^5 - 35/4*n^3 + 15/8*n)*Sn - 63/8*n^5 - 315/8*n^4 - 70*n^3 - 105/2*n^2 - 15*n - 1 and the initial conditions {0: 0, 1: 1, -1: -1}
            sage: l.to_polynomial()
            63/8*n^5 - 35/4*n^3 + 15/8*n

        """
        #don`t want to care about None entries
        max_pol = max(self.initial_conditions()) + 1
        
        R = self.parent().base_ring()
        n = R.gen()
        
        if self.__is_zero__():
            return R.zero()
        
        #computing a base of the solution space
        base = self.ann().polynomial_solutions()
        if len(base) == 0:
            raise TypeError, "the D-finite sequence does not come from a polynomial"
        
        #generating an equation system
        vars = list(var('x_%d' % i) for i in range(len(base)))
        c = [0]*len(base)
        for i in range(len(base)):
            base[i] = base[i][0]
            c[i] = base[i]*vars[i]
        poly = sum(c)
        eqs = list(poly(n = k) == self[k] for k in range(max_pol, len(base)+max_pol))
        
        #solving the system and putting results together
        result = solve(eqs,vars)
        if len(result) == 0:
            raise TypeError, "the D-finite sequence does not come from a polynomial"
        if type(result[0]) == list:
            result = result[0]
        coeffs_result = [0]*len(result)
        for i in range(len(result)):
            coeffs_result[i] = result[i].rhs()
        result = sum(list(a*b for a,b in zip(coeffs_result,base)))
        
        #checking if the polynomial also yields the correct values for all singularities (except from pols)
        if all(result(n = k) == self[k] for k in self.initial_conditions() if self[k] != None):
            return R(result)
        else:
            raise TypeError, "the D-finite sequence does not come from a polynomial"

    def to_rational(self):
        """
        Try to convert ``self`` into a rational function.
        
        OUTPUT:
        
        Either a rational function r(n) from the fraction field of the base ring of the OreAlgebra of the annihilating 
        operator of ``self`` such that self(n) = r(n) for all n in NN (eventually except from pols) or an error message
        if no such rational function exists.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D((n^2+3*n-4)/(n^5+4*n^3+10*n))
            sage: a.to_rational()
            (n^2 + 3*n - 4)/(n^5 + 4*n^3 + 10*n)
            sage: l = D(legendre_P(5,n)/legendre_P(3,n))
            sage: l
            Univariate D-finite sequence defined by the annihilating operator (1260*n^6 + 2520*n^5 - 896*n^4 - 2800*n^3 - 260*n^2 + 600*n + 120)*Sn - 1260*n^6 - 5040*n^5 - 5404*n^4 + 784*n^3 + 3536*n^2 + 1344*n + 96 and the initial conditions {0: -5/4}
            sage: l.to_rational()
            (63*n^4 - 70*n^2 + 15)/(20*n^2 - 12)
            
        """
        #don`t want to care about None entries
        max_pol = max(self.initial_conditions()) + 1
        
        R = self.parent().base_ring()
        n = R.gen()
        
        if self.__is_zero__():
            return R.fraction_field().zero()
        
        #computing a base of the solution space
        base = self.ann().rational_solutions()
        if len(base) == 0:
            raise TypeError, "the D-finite sequence does not come from a rational function"
        
        #generating an equation system
        vars = list(var('x_%d' % i) for i in range(len(base)))
        c = [0]*len(base)
        for i in range(len(base)):
            base[i] = base[i][0]
            c[i] = base[i]*vars[i]
        rat = sum(c)
        num = rat.numerator()
        denom = rat.denominator()
        eqs = list(num.subs(n = k) == denom.subs(n = k)*self[k] for k in range(max_pol, len(base)+max_pol))
        
        #solving the system and putting results together
        result = solve(eqs,vars)
        if len(result) == 0:
            raise TypeError, "the D-finite sequence does not come from a rational function"
        if type(result[0]) == list:
            result = result[0]
        coeffs_result = [0]*len(result)
        for i in range(len(result)):
            coeffs_result[i] = result[i].rhs()
        result = sum(list(a*b for a,b in zip(coeffs_result,base)))
        
        #checking if the ratinoal function also yields the correct values for all singularities (except from pols)
        if all(result(n = k) == self[k] for k in self.initial_conditions() if self[k] != None):
            return R.fraction_field()(result)
        else:
            raise TypeError, "the D-finite sequence does not come from a rational function"


    def generating_function(self):
        """
        """
        A = OreAlgebra(QQ['x'],'Dx')
        D = DFiniteFunctionRing(A)
        return UnivariateDFiniteFunction(D,self.ann().to_D(A),self)
    
    def __add_without_compress__(self,right):
        """
        Adds the D-finite sequences ``self`` and ``right`` without automatically trying
        to compress the result. This method is called whenever equality testing is done
        because in that case compressing the result would be unnecessary work.
        """
        #getting the operator
        N = self.parent().base_ring().gen()
        A = self.parent().ore_algebra()
        sum_ann = self.ann().lclm(right.ann())
        
        #getting the largest and smallest degree of the operator
        ord = sum_ann.order()
        min_degree = next((index for index, coeff in enumerate(sum_ann.list()) if coeff != 0), None)

        #initial values and singularities of the new operator
        singularities_positive = sum_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = sum_ann.singularities(True)
    
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_sum = {n:self[n] + right[n] if (self[n] != None and right[n] != None) else None for n in initial_val}

        #critical points for forward calculation
        critical_points_positive = self.critical_points(ord).union( right.critical_points(ord) )
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        
        for n in critical_points_positive:
            int_val_sum.update({n:self[n] + right[n] if (self[n] != None and right[n] != None) else None})
            sum_ann = A(N - (n - ord) )*sum_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                int_val_sum.update({(n-ord)+min_degree: self[(n-ord)+min_degree] + right[(n-ord)+min_degree] if (self[(n-ord)+min_degree] != None and right[(n-ord)+min_degree] != None) else None})
        
        #critical points for backward calculation
        critical_points_negative = self.critical_points(ord,True).union( right.critical_points(ord,True) )
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))
            
        for n in critical_points_negative:
            int_val_sum.update({n:self[n] + right[n] if (self[n] != None and right[n] != None) else None})
            sum_ann = A(N - (n - min_degree) )*sum_ann
            if n >= min_degree:
                int_val_sum.update({(n-min_degree)+ord:self[(n-min_degree)+ord] + right[(n-min_degree)+ord] if (self[(n-min_degree)+ord] != None and right[(n-min_degree)+ord] != None) else None})
                
        return UnivariateDFiniteSequence(self.parent(), sum_ann, int_val_sum)

#arithmetic

    def _add_(self, right):
        """
        Return the sum of ``self`` and ``right``.
        
        ``_add_`` uses the method ``lclm`` from the OreAlgebra package to get the new annihilator.
        If ``self`` or ``right`` contains a ``None`` value at a certain position, then the sum will also 
        have a ``None`` entry at this position.
        Additionally the result is automatically compressed using the compress() method.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A)
            sage: n = A.base_ring().gen()
            sage: a = UnivariateDFiniteSequence(D, Sn**2 - Sn - 1, [0,1])
            sage: b = D(harmonic_number(n))
            sage: c = a+b
            sage: c.expand(8)
            [0, 2, 5/2, 23/6, 61/12, 437/60, 209/20, 2183/140, 6641/280]
            sage: [a(i) + b(i) for i in range(9)]
            [0, 2, 5/2, 23/6, 61/12, 437/60, 209/20, 2183/140, 6641/280]
            
        """
        if self.__is_zero__():
            return right
        if right.__is_zero__():
            return self
        
        #getting the operator
        N = self.parent().base_ring().gen()
        A = self.parent().ore_algebra()
        sum_ann = self.ann().lclm(right.ann())
        
        #getting the largest and smallest degree of the operator
        ord = sum_ann.order()
        min_degree = next((index for index, coeff in enumerate(sum_ann.list()) if coeff != 0), None)

        #initial values and singularities of the new operator
        singularities_positive = sum_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = sum_ann.singularities(True)
    
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_sum = {n:self[n] + right[n] if (self[n] != None and right[n] != None) else None for n in initial_val}

        #critical points for forward calculation
        critical_points_positive = self.critical_points(ord).union( right.critical_points(ord) )
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        
        for n in critical_points_positive:
            int_val_sum.update({n:self[n] + right[n] if (self[n] != None and right[n] != None) else None})
            sum_ann = A(N - (n - ord) )*sum_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                int_val_sum.update({(n-ord)+min_degree: self[(n-ord)+min_degree] + right[(n-ord)+min_degree] if (self[(n-ord)+min_degree] != None and right[(n-ord)+min_degree] != None) else None})
        
        #critical points for backward calculation
        critical_points_negative = self.critical_points(ord,True).union( right.critical_points(ord,True) )
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))
            
        for n in critical_points_negative:
            int_val_sum.update({n:self[n] + right[n] if (self[n] != None and right[n] != None) else None})
            sum_ann = A(N - (n - min_degree) )*sum_ann
            if n >= min_degree:
                int_val_sum.update({(n-min_degree)+ord:self[(n-min_degree)+ord] + right[(n-min_degree)+ord] if (self[(n-min_degree)+ord] != None and right[(n-min_degree)+ord] != None) else None})
        
        sum = UnivariateDFiniteSequence(self.parent(), sum_ann, int_val_sum)

        return sum.compress()
        
    def _neg_(self):
        """
        Return the negative of ``self``.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D(n)
            sage: -a
            Univariate D-finite sequence defined by the annihilating operator n*Sn - n - 1 and the initial conditions {0: 0, 1: -1, -1: 1}
            sage: (-a).expand(10)
            [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10]

        """
        neg_int_val = {key:(-self._initial_values[key]) if (self._initial_values[key] != None) else None for key in self._initial_values}
        return UnivariateDFiniteSequence(self.parent(), self.ann(), neg_int_val)

    def _mul_(self, right):
        """
        Return the product of ``self`` and ``right``
        
        The result is the termwise product (Hadamard product) of ``self`` and ``right``. To get the cauchy product
        use the method ``cauchy_product``.
        ``_mul_`` uses the method ``symmetric_product`` of the OreAlgebra package to get the new annihilator. If ``self``
        or ``right`` contains a ``None`` value at a certain position, then the product will also have a ``None`` entry at this position.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D(n)
            sage: b = D(1/n)
            sage: c = a*b
            sage: c.expand(10)
            [None, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            
        """
        if self.__is_zero__() or right.__is_zero__():
            return self.parent().zero()
        
        #getting the operator
        N = self.parent().base_ring().gen()
        A = self.parent().ore_algebra()
        prod_ann = self.ann().symmetric_product(right.ann())
        
        #getting the largest and smallest degree of the operator
        ord = prod_ann.order()
        min_degree = next((index for index, coeff in enumerate(prod_ann.list()) if coeff != 0), None)

        #initial values and singularities of the new operator
        singularities_positive = prod_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = prod_ann.singularities(True)
    
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_prod = {n:self[n] * right[n] if (self[n] != None and right[n] != None) else None for n in initial_val }
        
        #critical points for forward calculation
        critical_points_positive = self.critical_points(ord).union( right.critical_points(ord) )
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        
        for n in critical_points_positive:
            int_val_prod.update({n:self[n] * right[n] if (self[n] != None and right[n] != None) else None})
            prod_ann = A(N - (n - ord) )*prod_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                int_val_prod.update({(n-ord)+min_degree: self[(n-ord)+min_degree] * right[(n-ord)+min_degree] if (self[(n-ord)+min_degree] != None and right[(n-ord)+min_degree] != None) else None})
        
        #critical points for backward calculation
        critical_points_negative = self.critical_points(ord,True).union( right.critical_points(ord,True) )
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))
        
        for n in critical_points_negative:
            int_val_prod.update({n:self[n] * right[n] if (self[n] != None and right[n] != None) else None})
            prod_ann = A(N-(n-min_degree))*prod_ann
            if n >= min_degree:
                int_val_prod.update({(n-min_degree)+ord:self[(n-min_degree)+ord] * right[(n-min_degree)+ord] if (self[(n-min_degree)+ord] != None and right[(n-min_degree)+ord] != None) else None})
        
        prod = UnivariateDFiniteSequence(self.parent(), prod_ann, int_val_prod)
        return prod
        
        
    def cauchy_product(self, right):
        """
        Return the cauchy product of ``self`` and ``right``
        
        The result is the cauchy product of ``self`` and ``right``. To get the termwise product (Hadamard product)
        use the method ``_mul_``.
        This method uses the method ``symmetric_product`` (but in an OreAlgebra with the differential operator) of the 
        OreAlgebra package to get the new annihilator. If ``self`` or ``right`` contains a ``None`` value at a certain position, 
        then the cauchy product will have ``None`` entries at this position and all positions afterwards.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D,"(n + 1)*Sn + n + 1", {0:1,-1:0}) #Taylor coefficients of 1/(x+1)
            sage: a.expand(10)
            [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1]
            sage: b = UnivariateDFiniteSequence(D,"(n + 1)*Sn + n - 1",{0:1,1:1}) #Taylor coefficients of x+1
            sage: b.expand(10)
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            sage: a.cauchy_product(b).expand(10)
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        """
        if self.__is_zero__() or right.__is_zero__():
            return self.parent().zero()
        
        #getting the operator
        R = self.parent().base_ring()
        N = R.gen()
        A = self.parent().ore_algebra()
        D = OreAlgebra(R.change_var('x'),'Dx')
        
        L = self.ann().to_D(D)
        M = right.ann().to_D(D)
        
        prod_ann = L.symmetric_product(M).to_S(A)
        
        #getting the largest and smallest degree of the operator
        ord = prod_ann.order()
        min_degree = next((index for index, coeff in enumerate(prod_ann.list()) if coeff != 0), None)
        
        #initial values and singularities of the new operator
        singularities_positive = prod_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = prod_ann.singularities(True)
    
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_prod = {}
        for n in initial_val:
            a = self.expand(n)
            b = right.expand(n)
            b.reverse()
            if all(x != None for x in a) and all(y != None for y in b):
                cauchy = sum([x*y for x,y in zip(a,b)])
            else:
                cauchy = None
            int_val_prod.update({n:cauchy})
        
        #critical points for forward calculation
        critical_points_positive = self.critical_points(ord).union( right.critical_points(ord) )
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        
        for n in critical_points_positive:
            a = self.expand(n)
            b = right.expand(n)
            b.reverse()
            if all(x != None for x in a) and all(y != None for y in b):
                cauchy = sum([x*y for x,y in zip(a,b)])
            else:
                cauchy = None
            int_val_prod.update({n:cauchy})
            prod_ann = A(N - (n - ord) )*prod_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                a = self.expand((n-ord)+min_degree)
                b = right.expand((n-ord)+min_degree)
                b.reverse()
                if all(x != None for x in a) and all(y != None for y in b):
                    cauchy = sum([x*y for x,y in zip(a,b)])
                else:
                    cauchy = None
                int_val_prod.update({(n-ord)+min_degree:cauchy})

        
        #critical points for backward calculation
        critical_points_negative = self.critical_points(ord,True).union( right.critical_points(ord,True) )
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))
        
        for n in critical_points_negative:
            a = self.expand(n)
            b = right.expand(n)
            b.reverse()
            if all(x != None for x in a) and all(y != None for y in b):
                cauchy = sum([x*y for x,y in zip(a,b)])
            else:
                cauchy = None
            int_val_prod.update({n:cauchy})
            prod_ann = A(N-(n-min_degree))*prod_ann
            if n >= min_degree:
                a = self.expand((n-min_degree)+ord)
                b = right.expand((n-min_degree)+ord)
                b.reverse()
                if all(x != None for x in a) and all(y != None for y in b):
                    cauchy = sum([x*y for x,y in zip(a,b)])
                else:
                    cauchy = None
                int_val_prod.update({(n-min_degree)+ord:cauchy})
    
        return UnivariateDFiniteSequence(self.parent(), prod_ann, int_val_prod)
        
    def __invert__(self):
        """
        """
        raise NotImplementedError
    
    def interlace(self, right):
        """
        Return the interlaced sequence of ``self`` and ``right``.
        ``interlace`` uses the method ``annihilator_of_interlacing`` of the OreAlgebra package to get the new operator.
        
        OUTPUT:
        
        If ``self`` is of the form a_0,a_1,a_2,\dots and ``right`` is of the form b_0,b_1,b_2,\dots, then
        the result is a UnivariateDFiniteSequence object that represents the sequence a_0,b_0,a_1,b_1,a_2,b_2,\dots
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: n = A.base_ring().gen()
            sage: a = D(n)
            sage: b = D(1/n)
            sage: c = a.interlace(b)
            sage: c.expand(10)
            [0, None, 1, 1, 2, 1/2, 3, 1/3, 4, 1/4, 5]
            
        """
        #getting the operator
        N = self.parent().base_ring().gen()
        A = self.parent().ore_algebra()
        interlacing_ann = self.ann().annihilator_of_interlacing(right.ann())
        
        #getting the largest and smallest degree of the operator
        ord = interlacing_ann.order()
        min_degree = next((index for index, coeff in enumerate(interlacing_ann.list()) if coeff != 0), None)
        
        #initial values and singularities of the new operator
        singularities_positive = interlacing_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = interlacing_ann.singularities(True)
        
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_interlacing = {}
        for n in initial_val:
            if n % 2 == 0:
                int_val_interlacing.update({n:self[n/2]})
            else:
                int_val_interlacing.update({n:right[floor(n/2)]})
        
        #critical points for forward calculation
        critical_points_positive = set()
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
                
        for n in self.critical_points(ord):
                critical_points_positive.update([2*n])
        for n in right.critical_points(ord):
                critical_points_positive.update([2*n+1])

        for n in critical_points_positive:
            if n % 2 == 0:
                int_val_interlacing.update({n:self[n/2]})
            else:
                int_val_interlacing.update({n:right[floor(n/2)]})
            interlacing_ann = A(N -(n - ord))*interlacing_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                if (n-ord+min_degree) % 2 == 0:
                    int_val_interlacing.update({n-ord+min_degree:self[(n-ord+min_degree)/2]})
                else:
                    int_val_interlacing.update({n-ord:right[floor((n-ord+min_degree)/2)]})

        #critical points for backward calculation
        critical_points_negative = set()
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))

        for n in self.critical_points(ord,True):
            critical_points_negative.update([2*n])
        for n in right.critical_points(ord,True):
            critical_points_negative.update([2*n+1])

        for n in critical_points_negative:
            if n % 2 == 0:
                int_val_interlacing.update({n:self[n/2]})
            else:
                int_val_interlacing.update({n:right[floor(n/2)]})
            interlacing_ann = A(N - (n-min_degree) )*interlacing_ann
            if n >= min_degree:
                if (n+ord) % 2 == 0:
                    int_val_interlacing.update({(n-min_degree) + ord:self[((n-min_degree)+ ord)/2]})
                else:
                    int_val_interlacing.update({(n-min_degree) + ord:right[floor(((n-min_degree)+ ord)/2)]})
        
        return UnivariateDFiniteSequence(self.parent(), interlacing_ann, int_val_interlacing)
        
    
    def sum(self):
        """
        Return the sequence (s_n)_{n=0}^\infty with s_n = \sum_{k=0}^n self[k].
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A)
            sage: n = A.base_ring().gen()
            sage: a = D(1/(n+1))
            sage: a.sum()
            Univariate D-finite sequence defined by the annihilating operator (n + 3)*Sn^2 + (-2*n - 5)*Sn + n + 2 and the initial conditions {0: 1, 1: 3/2}
            sage: _ == D(harmonic_number(n+1))
            True
            
        """
        #only makes sense for sequences over NN
        if self.parent().codomain() == ZZ:
            raise TypeError, "codomain of the DFiniteFunctionRing has to be NN"
        
        #getting the operator
        N = self.parent().base_ring().gen()
        A = self.parent().ore_algebra()
        sum_ann = self.ann().annihilator_of_sum()
    
        #getting the largest and smallest degree of the operator
        ord = sum_ann.order()
        min_degree = next((index for index, coeff in enumerate(sum_ann.list()) if coeff != 0), None)

        #initial values and singularities of the new operator
        singularities_positive = sum_ann.singularities()
        singularities_negative = set()
        if self.parent()._backward_calculation == True:
            singularities_negative = sum_ann.singularities(True)
    
        initial_val = set(range(ord)).union(singularities_positive, singularities_negative)
        int_val_sum = {n : sum(self.expand(n)) if all(self[k] != None for k in xrange(n+1)) else None for n in initial_val}

        #critical points for forward calculation
        critical_points_positive = self.critical_points(ord)
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
    
        for n in critical_points_positive:
            int_val_sum.update({n : sum(self.expand(n)) if all(self[k] != None for k in xrange(n+1)) else None})
            sum_ann = A(N - (n - ord) )*sum_ann
            if self.parent()._backward_calculation == True and n < ord - min_degree:
                int_val_sum.update({(n-ord)+min_degree : sum(self.expand((n-ord)+min_degree)) if all(self[k] != None for k in xrange((n-ord)+min_degree+1)) else None})
        
        #critical points for backward calculation
        critical_points_negative = self.critical_points(ord,True)
        for n in singularities_negative:
            critical_points_negative.update(range(n-ord,n))
            
        for n in critical_points_negative:
            int_val_sum.update({n : sum(self.expand(n)) if all(self[k] != None for k in xrange(n+1)) else None})
            sum_ann = A(N - (n - min_degree) )*sum_ann
            if n >= min_degree:
                int_val_sum.update({(n-min_degree)+ord : sum(self.expand((n-min_degree)+ord)) if all(self[k] != None for k in xrange((n-min_degree)+ord+1)) else None})

        return UnivariateDFiniteSequence(self.parent(), sum_ann, int_val_sum)
    
#evaluation
    
    def expand(self, n):
        """
        Return all the terms of ``self`` between 0 and ``n``
        
        INPUT:
        
        - ``n`` -- an integer; if ``self`` is defined over the codomain ZZ then ``n`` can also be negative
        
        OUTPUT:
        
        A list starting with the 0-th term up to the n-th term of ``self``.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D, "Sn^2 - Sn - 1", [0,1]) #the Fibonacci numbers
            sage: a.expand(10)
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            sage: a.expand(-10)
            [0, 1, -1, 2, -3, 5, -8, 13, -21, 34, -55]

        """
        ord = self.ann().order()
        start = 0
        
        if n >= 0:
            n = n+1
            #check if self is coming from a d-finite function that contains added zeros:
            if self.parent()._backward_calculation is False and min(self.initial_conditions()) < 0:
                start = -min(self.initial_conditions())
                n = n + start
            
            #1st case: n is smaller than the order - so all needed terms are already given
            if n < ord:
                return self.initial_values()[start:n]
        
        
            #2nd case: n is smaller than all relevant singularities - nothing to worry about
            s = [x for x in self.initial_conditions() if ord <= x]
            if all(n < x for x in s):
                return self.ann().to_list(self.initial_values(),n, -start)[start:]

            #3rd case: there is at least one singularity in the first n terms of the sequence
            s = set(x for x in self.initial_conditions() if ord <= x < n)
            r = self.initial_values()
            while s:
                m = min(s)
                if len(r) == m:
                    r.append(self._initial_values[m])
                else:
                    r2 = self.ann().to_list( r[len(r)-ord:], m-len(r)+ord, -start+len(r)-ord,true)
                    r = r + r2[ord:] + [self._initial_values[m]]
                s.remove(m)
            
            r2 = self.ann().to_list( r[len(r)-ord:], n-len(r)+ord, -start+len(r)-ord,true)
            r = r + r2[ord:]

            return r[start:]
      
        if n < 0:
            if self.parent()._backward_calculation is False:
                raise TypeError, "Backward Calculation is not possible - the D-finite function ring is not suitable"
            
            if ord != 0:
                ord = self.ann().order()-1
            N = self.parent().base_ring().gen()
                
            A = self.ann().annihilator_of_composition(ord-N)
                
            int_val = {ord-i:self[i] for i in self.initial_conditions() if i <= ord}
            if int_val:
                b = UnivariateDFiniteSequence(self.parent().change_codomain(NN), A, int_val)
                return b.expand(-(n+1)+ord+1)[ord:]
            else:
                return (-n+1)*[0]


    def __getitem__(self,n):
        """
        Return the n-th term of ``self``.
        
        INPUT:
        
        - ``n`` -- an integer; if ``self`` is defined over the codomain ZZ then ``n`` can also be negative

        OUTPUT:
        
        The n-th sequence term of ``self`` (starting with the 0-th, i.e. to get the first term one has to call ``self[0]``)
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['n'],'Sn')
            sage: D = DFiniteFunctionRing(A,ZZ)
            sage: a = UnivariateDFiniteSequence(D, "Sn^2 - Sn - 1", [0,1]) #the Fibonacci numbers
            sage: a[42]
            267914296
            sage: a[-100]
            -354224848179261915075
            
        """
        try:
            return self.initial_conditions()[n]
        except:
            pass
        
        ord = self.ann().order()
        if ord == 0:
            return 0
        
        #special case: n is negative
        if n < 0:
            return self.expand(n)[-n]
    
        #normal case: n >= 0
        if self.parent()._backward_calculation == False and min(self.initial_conditions()) < 0:
            start = min(self.initial_conditions())
        else:
            start = 0
        
        #handling None entries
        values = [self.initial_conditions()[i] for i in self.initial_conditions() if 0 <= i < n]
        if not all( x!= None for x in values):
            index = max([i for i in self.initial_conditions() if self.initial_conditions()[i] == None and 0 <= i < n])
            start += index+1
            int_val = [ self.initial_conditions()[i] for i in range(index+1,index+ord+1) ]
            roots = [ x - ord for x in self.singularities() if start <= x-ord <= n ]
        else:
            roots = [x - ord for x in self.singularities() if 0 <= x-ord <= n]
            int_val = self.initial_values()
        
        #handling singularities
        while len(roots) > 0:
            root = min(roots)
            Q,M = self.ann().forward_matrix_bsplit(ZZ(root-start),ZZ(start))
            v = Matrix([int_val]).transpose()/M
            result = Q * v
            if n < root + ord:
                d = n - (root+ord)
                return result[d][0]
            else:
                int_val = [result[i][0] for i in range(1,result.nrows())] + [self.initial_conditions()[root+ord]]
                start = root+1
                roots.remove(root)

        Q,M = self.ann().forward_matrix_bsplit(ZZ(n-start),ZZ(start))
        v = Matrix([int_val]).transpose()/M
        result = Q * v
        return result[0][0]

###############################################################################################################
class UnivariateDFiniteFunction(DFiniteFunction):
    """
    D-finite function in a single differentiable variable.
    """
    
#constructor
    
    def __init__(self, parent, ann, initial_val, is_gen=False, construct=False, cache=True):
        """
        Constructor for a D-finite function in a single differentiable variable.
        
         INPUT:
        
        - ``parent`` -- a DFiniteFunctionRing defined over an OreAlgebra with the differential operator
        
        - ``ann`` -- an annihilating operator, i.e. an element from the OreAlgebra over which the DFiniteFunctionRing is defined,
           that defines a differential equation for the function ``self`` should represent.
           
        - ``initial_val`` -- either a dictionary (or a list if no singularities occur) which contains the first r Taylor coefficients
          of ``self``, where r is the order of ``ann``, or a UnivariateDFiniteSequence which represents the Taylor sequence of ``self``
          
        OUTPUT:
        
        An object consisting of ``ann`` and a UnivariateDFiniteSequence that represents the D-finite function which is annihilated by ``ann``
        and has the Taylor sequence which is described by the UnivariateDFiniteSequence.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: x = A.base_ring().gen()
            sage: Dx = A.gen()
            sage: D1 = DFiniteFunctionRing(A)
            sage: UnivariateDFiniteFunction(D1,(3*x^2 + 4*x - 5)*Dx - 6*x - 4, {0:-5})
            Univariate D-finite function defined by the annihilating operator (3*x^2 + 4*x - 5)*Dx - 6*x - 4 and the coefficient sequence defined by (-5*n - 10)*Sn^2 + 4*n*Sn + 3*n - 6 and {0: -5, -1: 0}
            sage: B = OreAlgebra(QQ['n'],'Sn')
            sage: D2 = DFiniteFunctionRing(B)
            sage: coeffs = D2([1,-1,1,-1,1,-1])  #a UnivariateDFiniteSequence
            sage: UnivariateDFiniteFunction(D1,(x + 1)*Dx + 1, coeffs )
            Univariate D-finite function defined by the annihilating operator (x + 1)*Dx + 1 and the coefficient sequence defined by Sn + 1 and {0: 1}
        
        """
        if not parent.ore_algebra().is_D():
            raise TypeError, "Not the Differential Operator"
        super(UnivariateDFiniteFunction, self).__init__(parent, ann, initial_val, is_gen, construct, cache)
    
#action
    
    def __call__(self, r):
        """
        Lets ``self`` act on `r` and returns the result.
        `r` may be either a constant, then this (tries to) computes an evaluation. This evaluation might fail if there
        is a singularity of the annihilating operator of ``self`` between 0 and `r`. To then compute an evaluation use 
        ``evaluate`` and see the documentation there.
        `r` can also be a (suitable) expression, then the composition ``self(r)`` is computed. A suitable expression means 
        that `r` has to be a rational function (either in explicit form or in form of a UnivariateDFiniteFunction) whose first
        Taylor coefficient is 0.
        
        INPUT:
        
        - `r` -- either any data type that can be transformed into a float, or any data type that can be converted into a rational function
        
        OUTPUT:
        
        Either ``self`` evaluated at `r` (if possible) or the composition ``self(r)``
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: x = A.base_ring().gen()
            sage: D = DFiniteFunctionRing(A)
            sage: sin = D(sin(x))
            sage: f = 1/(x+1) - 1       #explicit rational function
            sage: g = D(1/(x+1) - 1)     #implicit form as a UnivariateDFiniteFunction
            sage: sin(f)
            Univariate D-finite function defined by the annihilating operator (-x^4 - 4*x^3 - 6*x^2 - 4*x - 1)*Dx^2 + (-2*x^3 - 6*x^2 - 6*x - 2)*Dx - 1 and the coefficient sequence defined by (-n^7 - 12*n^6 - 52*n^5 - 90*n^4 - 19*n^3 + 102*n^2 + 72*n)*Sn^4 + (-4*n^7 - 42*n^6 - 160*n^5 - 240*n^4 - 16*n^3 + 282*n^2 + 180*n)*Sn^3 + (-6*n^7 - 54*n^6 - 175*n^5 - 215*n^4 + 31*n^3 + 269*n^2 + 150*n)*Sn^2 + (-4*n^7 - 30*n^6 - 76*n^5 - 60*n^4 + 44*n^3 + 90*n^2 + 36*n)*Sn - n^7 - 6*n^6 - 10*n^5 + 11*n^3 + 6*n^2 and {0: 0, 1: -1, 2: 1, 3: -5/6, 4: 1/2, 5: -1/120}
            sage: sin(g)
            Univariate D-finite function defined by the annihilating operator (-x^4 - 4*x^3 - 6*x^2 - 4*x - 1)*Dx^2 + (-2*x^3 - 6*x^2 - 6*x - 2)*Dx - 1 and the coefficient sequence defined by (-n^7 - 12*n^6 - 52*n^5 - 90*n^4 - 19*n^3 + 102*n^2 + 72*n)*Sn^4 + (-4*n^7 - 42*n^6 - 160*n^5 - 240*n^4 - 16*n^3 + 282*n^2 + 180*n)*Sn^3 + (-6*n^7 - 54*n^6 - 175*n^5 - 215*n^4 + 31*n^3 + 269*n^2 + 150*n)*Sn^2 + (-4*n^7 - 30*n^6 - 76*n^5 - 60*n^4 + 44*n^3 + 90*n^2 + 36*n)*Sn - n^7 - 6*n^6 - 10*n^5 + 11*n^3 + 6*n^2 and {0: 0, 1: -1, 2: 1, 3: -5/6, 4: 1/2, 5: -1/120}
            sage: sin(pi)
            [1.224646799147353e-16 +/- 2.86e-32]

        """
        if type(r) == list:
            return self.evaluate(r,0)
        
        try:
            r = float(r)
        except:
            if not isinstance(r, UnivariateDFiniteFunction):
                r = self.parent()(r)
            
            A = self.parent().ore_algebra()
            R = A.base_ring()
            x = R.gen()
            if r[0] != 0:
                    raise ValueError, "constant term has to be zero"
        
            #getting the operator
            ann = self.ann().annihilator_of_composition(r.to_rational())
            S = OreAlgebra(R.change_var('n'),'Sn')
            s_ann = ann.to_S(S)
            ord = s_ann.order()
            
            #initial values and singularities of the new operator
            singularities_positive = s_ann.singularities()
                
            initial_val = set(range(ord)).union(singularities_positive)
            N = max(initial_val) + ord
            
            #computing the new coefficients
            B = sum( r[k]*x**k for k in range(1,N+2) )
            poly = sum( self[n]*B**n for n in range(N+1))
            
            int_val = {n:poly.derivative(n)(x=0)/factorial(n) for n in initial_val}

            #critical points for forward calculation
            critical_points_positive = self.critical_points(ord)
            for n in singularities_positive:
                critical_points_positive.update(range(n+1,n+ord+1))
        
            for n in critical_points_positive:
                int_val.update({ n : poly.derivative(n)(x=0)/factorial(n) })
                s_ann = S(s_ann.base_ring().gen() - (n - ord) )*s_ann
            
            seq = UnivariateDFiniteSequence(DFiniteFunctionRing(S,NN),s_ann,int_val)
        
            return UnivariateDFiniteFunction(self.parent(), ann, seq)
        
        return self.evaluate(r,0)
        
    def _test_conversion_(self):
        """
        Test whether a conversion of ``self`` into an int/float/long/... is possible;
        i.e. whether the function is constant or not.
        
        OUTPUT:
        
        If ``self`` is constant, i.e. all but the 0-th coefficient of ``self`` are 0, then the 0-th coefficient
        is returned (as an element of QQ). Otherwise ``None`` is returned.
        
        EXAMPLES::
            
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(3.4)
            sage: b = D(x)
            sage: a._test_conversion_()
            17/5
            sage: b._test_conversion_()
            #None is returend
            
        """
        ini = self.initial_conditions()
        
        if all(x == 0 for x in ini.initial_conditions() if x != 0):
            Dx = self.parent().ore_algebra().gen()
            if self.ann().quo_rem(Dx)[1].is_zero():
                return ini[0]
        return None
        
    def to_polynomial(self):
        """
        Try to convert ``self`` into a polynomial.
        
        OUTPUT:
        
        Either a polynomial f(x) from the base ring of the OreAlgebra of the annihilating operator of ``self`` such that
        f(x) is the explicit form of ``self`` (if ``self`` represents a polynomial) or an error message if no such polynomial exists.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(3*x^3 + 5*x - 10)
            sage: a.to_polynomial()
            3*x^3 + 5*x - 10
            sage: l = D(legendre_P(5,x))
            sage: l
            Univariate D-finite function defined by the annihilating operator (63/8*x^5 - 35/4*x^3 + 15/8*x)*Dx - 315/8*x^4 + 105/4*x^2 - 15/8 and the coefficient sequence defined by (15/8*n + 45/8)*Sn^4 + (-35/4*n + 35/4)*Sn^2 + 63/8*n - 315/8 and {0: 0, 1: 15/8, 2: 0, 3: -35/4}
            sage: l.to_polynomial()
            63/8*x^5 - 35/4*x^3 + 15/8*x

        """
        R = self.parent().base_ring()
        x = R.gen()
        
        if self.__is_zero__():
            return R.zero()
        
        #computing a base of the solution space
        base = self.ann().polynomial_solutions()
        if len(base) == 0:
            raise TypeError, "the D-finite function is not a polynomial"
        
        #generating an equation system
        vars = list(var('x_%d' % i) for i in range(len(base)))
        c = [0]*len(base)
        for i in range(len(base)):
            base[i] = base[i][0]
            c[i] = base[i]*vars[i]
        coeffs = sum(c).coefficients(x,False)
        int_val = self.expand(len(coeffs)-1)
        eqs = list(coeffs[k] == int_val[k] for k in range(len(coeffs)))
        
        #solving the system and putting results together
        result = solve(eqs,vars)
        if len(result) == 0:
            raise TypeError, "the D-finite function is not a polynomial"
        if type(result[0]) == list:
            result = result[0]
        coeffs_result = [0]*len(result)
        for i in range(len(result)):
            coeffs_result[i] = result[i].rhs()
        poly = sum(list(a*b for a,b in zip(coeffs_result,base)))
        
        if all(poly.derivative(k)(x=0)/factorial(k) == self[k] for k in self.initial_conditions().initial_conditions() if (self[k] != None and k>=0)):
            return R(poly)
        else:
            raise TypeError, "the D-finite function is not a polynomial"

    def to_rational(self):
        """
        Try to convert ``self`` into a rational function.
        
        OUTPUT:
        
        Either a rational function r(x) from the fraction field of the base ring of the OreAlgebra of the annihilating
        operator of ``self`` such that r(x) is the explicit form of ``self`` (if ``self`` represents a rational function) or
        an error message if no such function exists.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D((x^2+3*x-4)/(x^5+4*x^3+10))
            sage: a.to_rational()
            (x^2 + 3*x - 4)/(x^5 + 4*x^3 + 10)
            sage: l = D(legendre_P(5,x)/legendre_P(3,x))
            sage: l
            Univariate D-finite function defined by the annihilating operator (1260*x^6 - 2156*x^4 + 1140*x^2 - 180)*Dx - 2520*x^5 + 3024*x^3 - 1080*x and the coefficient sequence defined by (-180*n - 1080)*Sn^6 + (1140*n + 3480)*Sn^4 + (-2156*n - 1288)*Sn^2 + 1260*n - 2520 and {0: -5/4, 1: 0, 2: 15/4, 3: 0, 4: 1, 5: 0}
            sage: l.to_rational()
            (63*x^4 - 70*x^2 + 15)/(20*x^2 - 12)
            
        """
        R = self.parent().base_ring()
        x = R.gen()
        
        if self.__is_zero__():
            return R.fraction_field().zero()
        
        #computing a base of the solution space
        base = self.ann().rational_solutions()
        if len(base) == 0:
            raise TypeError, "the D-finite function is not a rational function"
        
        #generating an equation system
        vars = list(var('a_%d' % i) for i in range(len(base)))
        c = [0]*len(base)
        for i in range(len(base)):
            base[i] = base[i][0]
            c[i] = base[i]*vars[i]
        
        rat = sum(c)
        coeffs_num = rat.numerator().coefficients(x,False)
        coeffs_denom = rat.denominator().coefficients(x,False)
        
        eqs = []
        for k in range(len(coeffs_num)):
            eqs.append( coeffs_num[k] == sum(coeffs_denom[i]*self[k-i] for i in range(len(coeffs_denom))) )
        
        #solving the system and putting results together
        result = solve(eqs,vars)
        if len(result) == 0:
            raise TypeError, "the D-finite function is not a rational function"
        if type(result[0]) == list:
            result = result[0]
        coeffs_result = list( result[i].rhs() for i in range(len(result)) )
        result = sum(list(a*b for a,b in zip(coeffs_result,base)))

        if all(result.derivative(k)(x=0)/factorial(k) == self[k] for k in self.initial_conditions().initial_conditions() if (self[k] != None and k >= 0)):
            return R.fraction_field()(result)
        else:
            raise TypeError, "the D-finite function is not a rational function"

    def __add_without_compress__(self,right):
        """
        Adds the D-finite functions ``self`` and ``right`` without automatically trying
        to compress the result. This method is called whenever equality testing is done
        because there compressing the result would be unnecessary work.
        """
        sum_ann = self.ann().lclm(right.ann())
        
        lseq = self.initial_conditions()
        rseq = right.initial_conditions()

        seq = lseq.__add_without_compress__(rseq)
    
        return UnivariateDFiniteFunction(self.parent(), sum_ann, seq)


#evaluation

    def dict(self):
        raise NotImplementedError
    
    def list(self):
        raise NotImplementedError
    
    def expand(self, n, deriv = False):
        """
        Return a list of the first `n+1` coefficients of ``self`` if ``deriv``is False.
        If ``deriv`` is True the first `n+1` derivations of self at x=0 are returned.
        
        INPUT:
        
        - `n` -- a non-negative integer
        
        - ``deriv`` (default ``False``) -- boolean value. Determines whether the coefficients (default) or derivations of ``self`` are returned
    
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: e = D(exp(x))
            sage: e.expand(10)
            [1, 1, 1/2, 1/6, 1/24, 1/120, 1/720, 1/5040, 1/40320, 1/362880, 1/3628800]
            sage: e.expand(10,True)
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        """
        result = self._initial_values.expand(n)
        if deriv == True:
            result = [result[i]* factorial(i) for i in range(len(result))]
        
        return result
    
#arithmetic
    
    def _add_(self, right):
        """
        Returns the sum of ``self`` and ``right``
        ``_add_`` uses the method ``lclm`` from the OreAlgebra package to get the new annihilator.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(3*x^2 + 4)
            sage: e = D(exp(x))
            sage: s = a+e
            sage: a.expand(10)
            [4, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0]
            sage: e.expand(10)
            [1, 1, 1/2, 1/6, 1/24, 1/120, 1/720, 1/5040, 1/40320, 1/362880, 1/3628800]
            sage: s.expand(10)
            [5, 1, 7/2, 1/6, 1/24, 1/120, 1/720, 1/5040, 1/40320, 1/362880, 1/3628800]
            
        """
        if self.__is_zero__():
            return right
        if right.__is_zero__():
            return self
        
        sum_ann = self.ann().lclm(right.ann())
        
        lseq = self.initial_conditions()
        rseq = right.initial_conditions()

        seq = lseq + rseq
    
        return UnivariateDFiniteFunction(self.parent(), sum_ann, seq).compress()
        
    
    def _neg_(self):
        """
        Return the negative of ``self``
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(1/(x-1))
            sage: a.expand(10)
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
            sage: -a
            Univariate D-finite function defined by the annihilating operator (x - 1)*Dx + 1 and the coefficient sequence defined by (-n - 1)*Sn + n + 1 and {0: 1}
            sage: (-a).expand(10)
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        
        """
        return UnivariateDFiniteFunction(self.parent(), self.ann(),  -self._initial_values)
    
    
    def _mul_(self, right):
        """
        Return the product of ``self`` and ``right``
        ``_mul_`` uses the method ``symmetric_product`` from the OreAlgebra package to get the new annihilator.
        Here we do not use the method ``cauchy_product`` from the class UnivariateDFiniteSequence, even though it would
        lead to the same (correct) result. But to use that method one would have to use (more) transformations of the annihilating operators
        beetween the differential and the shift OreAlgebra, which would increase their orders (even more) and would eventually lead to an increased
        computation time.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(1/(x+1))
            sage: b = D(x+1)
            sage: p = a*b
            sage: p
            Univariate D-finite function defined by the annihilating operator Dx and the coefficient sequence defined by n^2 and {0: 1}
            sage: p.to_polynomial()
            1
            
        """
        if self.__is_zero__() or right.__is_zero__():
            return self.parent().zero()
        
        if self == self.parent().one():
            return right
        if right == self.parent().one():
            return self
        
        lseq = self.initial_conditions()
        rseq = right.initial_conditions()
        
        #getting the new operators
        prod_ann = self.ann().symmetric_product(right.ann())
        A = OreAlgebra(self.parent().base_ring().change_var('n'),'Sn')
        N = A.base_ring().gen()
        s_ann = prod_ann.to_S(A)
        ord = s_ann.order()

        #initial values and singularities of the sequence operator
        singularities_positive = s_ann.singularities()
    
        initial_val = set(range(ord)).union(singularities_positive)
        int_val_prod = {}
        for n in initial_val:
            a = lseq.expand(n)
            b = rseq.expand(n)
            b.reverse()
            cauchy = sum([x*y for x,y in zip(a,b)])
            int_val_prod.update({n:cauchy})
        
        #critical points for forward calculation
        critical_points_positive = lseq.critical_points(ord).union( rseq.critical_points(ord) )
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        
        for n in critical_points_positive:
            a = lseq.expand(n)
            b = rseq.expand(n)
            b.reverse()
            cauchy = sum([x*y for x,y in zip(a,b)])
            int_val_prod.update({n:cauchy})
            s_ann = A(N - (n - ord) )*s_ann
        
        seq = UnivariateDFiniteSequence(DFiniteFunctionRing(A,NN),s_ann,int_val_prod)
    
        prod = UnivariateDFiniteFunction(self.parent(), prod_ann, seq)
        return prod
               
        
    def __invert__(self):
        """
        """
        raise NotImplementedError
    
    def integral(self):
        """
        Return the D-finite function corresponding to the integral of ``self``.
        By integral the formal integral of a power series is meant, i.e. 
        \int a(x) = \int_0^x \sum_{n=0}^\infty a_n x^n = \sum_{n=0}^\infty \frac{a_n}{n+1} x^{n+1}
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ[x],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: c = D(cos(x))
            sage: c.integral()
            Univariate D-finite function defined by the annihilating operator Dx^3 + Dx and the coefficient sequence defined by (n^7 + n^6 - 5*n^5 - 5*n^4 + 4*n^3 + 4*n^2)*Sn^2 + n^5 - 2*n^4 - n^3 + 2*n^2 and {0: 0, 1: 1, 2: 0, 3: -1/6, 4: 0}
            sage: _ == D(sin(x))
            True
        
        """
        #getting the new operators
        ann = self.ann().annihilator_of_integral()
        A = OreAlgebra(self.parent().base_ring().change_var('n'),'Sn')
        N = A.base_ring().gen()
        s_ann = ann.to_S(A)
        ord = s_ann.order()

        #initial values and singularities of the sequence operator
        singularities_positive = s_ann.singularities()
    
        initial_val = set(range(ord)).union(singularities_positive)
        int_val = {n:self[n-1]/QQ(n) for n in initial_val if n > 0}
        int_val.update({0:0})
        
        #critical points for forward calculation
        critical_points_positive = self.initial_conditions().critical_points(ord)
        for n in singularities_positive:
            critical_points_positive.update(range(n+1,n+ord+1))
        critical_points_positive.difference_update({0})
        
        for n in critical_points_positive:
            int_val.update({n:self[n-1]/n})
            s_ann = A(N - (n - ord) )*s_ann
        
        seq = UnivariateDFiniteSequence(DFiniteFunctionRing(A,NN),s_ann,int_val)
        integral = UnivariateDFiniteFunction(self.parent(), ann, seq)
        return integral
    
#evaluation

    def __getitem__(self, n):
        """
        Return the n-th coefficient of ``self`` (starting with 0).
        
        INPUT:
        
        - `n` -- an integer (`n` can also be negative)
        
        OUTPUT:
        
        If `n` is positive, then the n-th coefficient of ``self`` is returned (starting with the 0-th).
        If `n` is negative, then always 0 is returned.
        
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: f = D(3*x^113 + 5*x^2 + 13)
            sage: f[113]
            3
            sage: f[-12]
            0
        
        """
        if n >= 0:
            return self.initial_conditions()[n]
        else:
            return 0
    
    
    def evaluate(self, z, n = 0):
        """
        Tries to numerically evaluate the n-th derivative of ``self`` at  `z`
        
        INPUT:
        
        - `z` -- either a datatype that can be transformed into a float or a list of floating point numbers starting with 0 and ending
          with the value that which the derivation should be computed. The list should provide a path from 0 to the evaluation point, not 
          crossing any singularities of the annihilating operator of ``self`` (for further information see the documentation of the method
          ``numerical_solution`` of the OreAlgebra package).
          
        - `n` (default 0) -- a non-negative integer
        
        OUTPUT:
        
        The evaluation of the n-th derivative of ``self`` at `z` if `z` is a floating point number. If
        `z` is a list, then the evaluation of the n-th derivative of ``self`` at the last point of the list
        is computed.
            
        EXAMPLES::
        
            sage: A = OreAlgebra(QQ['x'],'Dx')
            sage: D = DFiniteFunctionRing(A)
            sage: x = A.base_ring().gen()
            sage: a = D(3*x^5 + 4*x^2 - 8*x +13)
            sage: sin = D(sin(x))
            sage: a.evaluate(0,0)
            13.00000000000000
            sage: a.evaluate(0,1)
            [-8.00000000000000 +/- 4.11e-15]
            sage: sin.evaluate(pi/2,0)
            [1.00000000000000 +/- 2.23e-16]
            sage: sin.evaluate(pi,1)
            [-1.00000000000000 +/- 2.23e-16]
            
        """
        ini = self.initial_values()
        Dx = self.parent().ore_algebra().gen()
        
        try:
            z = float(z)
            if z == 0:
                return self[0]
        except:
            pass
        
        if type(z) == float:
            return self.ann().numerical_solution(ini,[0,z], eps=1e-50, post_transform=Dx**n)
        elif type(z) == list:
            return self.ann().numerical_solution(ini,z, eps=1e-50, post_transform=Dx**n)
        else:
            raise NotImplementedError, "evalutation point has to be given in form of a single point or in form of a list"

