r"""
Monoids
"""
#*****************************************************************************
#  Copyright (C) 2005      David Kohel <kohel@maths.usyd.edu>
#                          William Stein <wstein@math.ucsd.edu>
#                2008      Teresa Gomez-Diaz (CNRS) <Teresa.Gomez-Diaz@univ-mlv.fr>
#                2008-2009 Florent Hivert <florent.hivert at univ-rouen.fr>
#                2008-2014 Nicolas M. Thiery <nthiery at users.sf.net>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
#******************************************************************************
from six.moves import range

from sage.misc.cachefunc import cached_method
from sage.misc.misc_c import prod
from sage.categories.category_with_axiom import CategoryWithAxiom
from sage.categories.semigroups import Semigroups
from sage.misc.lazy_import import LazyImport
from sage.categories.subquotients import SubquotientsCategory
from sage.categories.cartesian_product import CartesianProductsCategory
from sage.categories.algebra_functor import AlgebrasCategory
from sage.categories.with_realizations import WithRealizationsCategory
from sage.categories.finite_enumerated_sets import FiniteEnumeratedSets
from sage.structure.element import generic_power

class Monoids(CategoryWithAxiom):
    r"""
    The category of (multiplicative) monoids.

    A *monoid* is a unital :class:`semigroup <Semigroups>`, that is a
    set endowed with a multiplicative binary operation `*` which is
    associative and admits a unit (see :wikipedia:`Monoid`).

    EXAMPLES::

        sage: Monoids()
        Category of monoids
        sage: Monoids().super_categories()
        [Category of semigroups, Category of unital magmas]
        sage: Monoids().all_super_categories()
        [Category of monoids,
         Category of semigroups,
         Category of unital magmas, Category of magmas,
         Category of sets,
         Category of sets with partial maps,
         Category of objects]

        sage: Monoids().axioms()
        frozenset({'Associative', 'Unital'})
        sage: Semigroups().Unital()
        Category of monoids

        sage: Monoids().example()
        An example of a monoid: the free monoid generated by ('a', 'b', 'c', 'd')

    TESTS::

        sage: C = Monoids()
        sage: TestSuite(C).run()

    """

    _base_category_class_and_axiom = (Semigroups, "Unital")

    Finite = LazyImport('sage.categories.finite_monoids', 'FiniteMonoids', at_startup=True)
    Inverse = LazyImport('sage.categories.groups', 'Groups', at_startup=True)

    @staticmethod
    def free(index_set=None, names=None, **kwds):
        r"""
        Return a free monoid on `n` generators or with the generators
        indexed by a set `I`.

        A free monoid is constructed by specifing either:

        - the number of generators and/or the names of the generators
        - the indexing set for the generators

        INPUT:

        - ``index_set`` -- (optional) an index set for the generators; if
          an integer, then this represents `\{0, 1, \ldots, n-1\}`

        - ``names`` -- a string or list/tuple/iterable of strings
          (default: ``'x'``); the generator names or name prefix

        EXAMPLES::

            sage: Monoids.free(index_set=ZZ)
            Free monoid indexed by Integer Ring
            sage: Monoids().free(ZZ)
            Free monoid indexed by Integer Ring
            sage: F.<x,y,z> = Monoids().free(); F
            Free monoid indexed by {'x', 'y', 'z'}
        """
        if names is not None:
            if isinstance(names, str):
                from sage.rings.all import ZZ
                if ',' not in names and index_set in ZZ:
                    names = [names + repr(i) for i in range(index_set)]
                else:
                    names = names.split(',')
            names = tuple(names)
            if index_set is None:
                index_set = names

        from sage.monoids.indexed_free_monoid import IndexedFreeMonoid
        return IndexedFreeMonoid(index_set, names=names, **kwds)

    class ParentMethods:

        def one_element(self):
            r"""
            Backward compatibility alias for :meth:`one`.

            TESTS::

                sage: S = Monoids().example()
                sage: S.one_element()
                doctest:...: DeprecationWarning: .one_element() is deprecated. Please use .one() instead.
                See http://trac.sagemath.org/17694 for details.
                ''
            """
            from sage.misc.superseded import deprecation
            deprecation(17694, ".one_element() is deprecated. Please use .one() instead.")
            return self.one()

        def semigroup_generators(self):
            """
            Return the generators of ``self`` as a semigroup.

            The generators of a monoid `M` as a semigroup are the generators
            of `M` as a monoid and the unit.

            EXAMPLES::

                sage: M = Monoids().free([1,2,3])
                sage: M.semigroup_generators()
                Family (1, F[1], F[2], F[3])
            """
            G = self.monoid_generators()
            from sage.categories.finite_enumerated_sets import FiniteEnumeratedSets
            if G not in FiniteEnumeratedSets():
                raise NotImplementedError("currently only implemented for finitely generated monoids")
            from sage.sets.family import Family
            return Family((self.one(),) + tuple(G))

        def prod(self, args):
            r"""
            n-ary product of elements of ``self``.

            INPUT:

            - ``args`` -- a list (or iterable) of elements of ``self``

            Returns the product of the elements in ``args``, as an element of
            ``self``.

            EXAMPLES::

                sage: S = Monoids().example()
                sage: S.prod([S('a'), S('b')])
                'ab'
            """
            return prod(args, self.one())

        def _test_prod(self, **options):
            r"""
            Run basic tests for the product method :meth:`prod` of ``self``.

            See the documentation for :class:`TestSuite` for information on
            further options.

            INPUT:

            - ``options`` -- any keyword arguments accepted by :meth:`_tester`

            EXAMPLES:

            By default, this method tests only the elements returned by
            ``self.some_elements()``::

                sage: S = Monoids().example()
                sage: S._test_prod()

            However, the elements tested can be customized with the
            ``elements`` keyword argument::

                sage: S._test_prod(elements = (S('a'), S('b')))
            """
            tester = self._tester(**options)
            tester.assert_(self.prod([]) == self.one())
            for x in tester.some_elements():
                tester.assert_(self.prod([x]) == x)
                tester.assert_(self.prod([x, x]) == x**2)
                tester.assert_(self.prod([x, x, x]) == x**3)


        def submonoid(self, generators, category=None):
            r"""
            Return the multiplicative submonoid generated by ``generators``.

            INPUT:

            - ``generators`` -- a finite family of elements of
              ``self``, or a list, iterable, ... that can be converted
              into one (see :class:`Family`).

            - ``category`` -- a category

            This is a shorthand for
            :meth:`Semigroups.ParentMethods.subsemigroup` that
            specifies that this is a submonoid, and in particular that
            the unit is ``self.one()``.

            EXAMPLES::

                sage: R = IntegerModRing(15)
                sage: M = R.submonoid([R(3),R(5)]); M
                A submonoid of (Ring of integers modulo 15) with 2 generators
                sage: M.list()
                [1, 3, 5, 9, 0, 10, 12, 6]

            Not the presence of the unit, unlike in::

                sage: S = R.subsemigroup([R(3),R(5)]); S
                A subsemigroup of (Ring of integers modulo 15) with 2 generators
                sage: S.list()
                [3, 5, 9, 0, 10, 12, 6]

            This method is really a shorthand for subsemigroup::

                sage: M2 = R.subsemigroup([R(3),R(5)], one=R.one())
                sage: M2 is M
                True


            """
            return self.subsemigroup(generators, one=self.one())

    class ElementMethods:

        def is_one(self):
            r"""
            Return whether ``self`` is the one of the monoid.

            The default implementation is to compare with ``self.one()``.

            TESTS::

                sage: S = Monoids().example()
                sage: S.one().is_one()
                True
                sage: S("aa").is_one()
                False
            """
            return self == self.parent().one()

        def __pow__(self, n):
            r"""
            Return ``self`` to the `n^{th}` power.

            INPUT:

            - ``n`` -- a nonnegative integer

            EXAMPLES::

                sage: S = Monoids().example()
                sage: x = S("aa")
                sage: x^0, x^1, x^2, x^3, x^4, x^5
                ('', 'aa', 'aaaa', 'aaaaaa', 'aaaaaaaa', 'aaaaaaaaaa')

            """
            if not n: # FIXME: why do we need to do that?
                return self.parent().one()
            return generic_power(self, n, self.parent().one())

        def _pow_naive(self, n):
            r"""
            Return ``self`` to the `n^{th}` power (naive implementation).

            INPUT:

            - ``n`` -- a nonnegative integer

            This naive implementation does not use binary
            exponentiation; there are cases where this is actually
            faster due to size explosion.

            EXAMPLES::

                sage: S = Monoids().example()
                sage: x = S("aa")
                sage: [x._pow_naive(i) for i in range(6)]
                ['', 'aa', 'aaaa', 'aaaaaa', 'aaaaaaaa', 'aaaaaaaaaa']
            """
            if not n:
                return self.parent().one()
            result = self
            for i in range(n - 1):
                result *= self
            return result

        def powers(self, n):
            r"""
            Return the list `[x^0, x^1, \ldots, x^{n-1}]`.

            EXAMPLES::

                sage: A = Matrix([[1, 1], [-1, 0]])
                sage: A.powers(6)
                [
                [1 0]  [ 1  1]  [ 0  1]  [-1  0]  [-1 -1]  [ 0 -1]
                [0 1], [-1  0], [-1 -1], [ 0 -1], [ 1  0], [ 1  1]
                ]
            """
            if n < 0:
                raise ValueError("negative number of powers requested")
            elif n == 0:
                return []
            x = self.parent().one()
            l = [x]
            for i in range(n - 1):
                x = x * self
                l.append(x)
            return l

    class Commutative(CategoryWithAxiom):
        """
        Category of commutative (abelian) monoids.

        A monoid `M` is *commutative* if `xy = yx` for all `x,y \in M`.
        """
        @staticmethod
        def free(index_set=None, names=None, **kwds):
            r"""
            Return a free abelian monoid on `n` generators or with
            the generators indexed by a set `I`.

            A free monoid is constructed by specifing either:

            - the number of generators and/or the names of the generators, or
            - the indexing set for the generators.

            INPUT:

            - ``index_set`` -- (optional) an index set for the generators; if
              an integer, then this represents `\{0, 1, \ldots, n-1\}`

            - ``names`` -- a string or list/tuple/iterable of strings
              (default: ``'x'``); the generator names or name prefix

            EXAMPLES::

                sage: Monoids.Commutative.free(index_set=ZZ)
                Free abelian monoid indexed by Integer Ring
                sage: Monoids().Commutative().free(ZZ)
                Free abelian monoid indexed by Integer Ring
                sage: F.<x,y,z> = Monoids().Commutative().free(); F
                Free abelian monoid indexed by {'x', 'y', 'z'}
            """
            if names is not None:
                if isinstance(names, str):
                    from sage.rings.all import ZZ
                    if ',' not in names and index_set in ZZ:
                        names = [names + repr(i) for i in range(index_set)]
                    else:
                        names = names.split(',')
                names = tuple(names)
                if index_set is None:
                    index_set = names

            from sage.monoids.indexed_free_monoid import IndexedFreeAbelianMonoid
            return IndexedFreeAbelianMonoid(index_set, names=names, **kwds)

    class WithRealizations(WithRealizationsCategory):

        class ParentMethods:

            def one(self):
                r"""
                Return the unit of this monoid.

                This default implementation returns the unit of the
                realization of ``self`` given by
                :meth:`~Sets.WithRealizations.ParentMethods.a_realization`.

                EXAMPLES::

                    sage: A = Sets().WithRealizations().example(); A
                    The subset algebra of {1, 2, 3} over Rational Field
                    sage: A.one.__module__
                    'sage.categories.monoids'
                    sage: A.one()
                    F[{}]

                TESTS::

                    sage: A.one() is A.a_realization().one()
                    True
                    sage: A._test_one()
                """
                return self.a_realization().one()

    class Subquotients(SubquotientsCategory):

        class ParentMethods:

            def one(self):
                """
                Returns the multiplicative unit of this monoid,
                obtained by retracting that of the ambient monoid.

                EXAMPLES::

                    sage: S = Monoids().Subquotients().example() # todo: not implemented
                    sage: S.one()                                # todo: not implemented
                """
                return self.retract(self.ambient().one())

    class Algebras(AlgebrasCategory):

        def extra_super_categories(self):
            """
            EXAMPLES::

                sage: Monoids().Algebras(QQ).extra_super_categories()
                [Category of monoids]
                sage: Monoids().Algebras(QQ).super_categories()
                [Category of algebras with basis over Rational Field,
                 Category of semigroup algebras over Rational Field,
                 Category of unital magma algebras over Rational Field]
            """
            return [Monoids()]

        class ParentMethods:

            @cached_method
            def one_basis(self):
                """
                Return the unit of the monoid, which indexes the unit of
                this algebra, as per
                :meth:`AlgebrasWithBasis.ParentMethods.one_basis()
                <sage.categories.algebras_with_basis.AlgebrasWithBasis.ParentMethods.one_basis>`.

                EXAMPLES::

                    sage: A = Monoids().example().algebra(ZZ)
                    sage: A.one_basis()
                    ''
                    sage: A.one()
                    B['']
                    sage: A(3)
                    3*B['']
                """
                return self.basis().keys().one()

            @cached_method
            def algebra_generators(self):
                r"""
                Return generators for this algebra.

                For a monoid algebra, the algebra generators are built
                from the monoid generators if available and from the
                semigroup generators otherwise.

                .. SEEALSO::

                    - :meth:`Semigroups.Algebras.ParentMethods.algebra_generators`
                    - :meth:`MagmaticAlgebras.ParentMethods.algebra_generators()
                      <.magmatic_algebras.MagmaticAlgebras.ParentMethods.algebra_generators>`.

                EXAMPLES::

                    sage: M = Monoids().example(); M
                    An example of a monoid:
                    the free monoid generated by ('a', 'b', 'c', 'd')
                    sage: M.monoid_generators()
                    Finite family {'a': 'a', 'c': 'c', 'b': 'b', 'd': 'd'}
                    sage: M.algebra(ZZ).algebra_generators()
                    Finite family {'a': B['a'], 'c': B['c'], 'b': B['b'], 'd': B['d']}

                    sage: Z12 = Monoids().Finite().example(); Z12
                    An example of a finite multiplicative monoid:
                    the integers modulo 12
                    sage: Z12.monoid_generators()
                    Traceback (most recent call last):
                    ...
                    AttributeError: 'IntegerModMonoid_with_category' object
                    has no attribute 'monoid_generators'
                    sage: Z12.semigroup_generators()
                    Family (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
                    sage: Z12.algebra(QQ).algebra_generators()
                    Finite family {0: B[0], 1: B[1], 2: B[2], 3: B[3],  4: B[4],   5: B[5],
                                   6: B[6], 7: B[7], 8: B[8], 9: B[9], 10: B[10], 11: B[11]}


                    sage: GroupAlgebras(QQ).example(AlternatingGroup(10)).algebra_generators()
                    Finite family {0: (8,9,10), 1: (1,2,3,4,5,6,7,8,9)}

                    sage: A = DihedralGroup(3).algebra(QQ); A
                    Algebra of Dihedral group of order 6 as a permutation group
                     over Rational Field
                    sage: A.algebra_generators()
                    Finite family {0: (1,2,3), 1: (1,3)}
                """
                monoid = self.basis().keys()
                try:
                    generators = monoid.monoid_generators()
                except AttributeError:
                    generators = monoid.semigroup_generators()
                return generators.map(self.monomial)

        class ElementMethods:

            def is_central(self):
                r"""
                Return whether the element ``self`` is central.

                EXAMPLES::

                    sage: SG4=SymmetricGroupAlgebra(ZZ,4)
                    sage: SG4(1).is_central()
                    True
                    sage: SG4(Permutation([1,3,2,4])).is_central()
                    False
                    sage: A=GroupAlgebras(QQ).example(); A
                    Algebra of Dihedral group of order 8 as a permutation group over Rational Field
                    sage: sum(i for i in A.basis()).is_central()
                    True
                """
                return all([i*self == self*i for i in self.parent().algebra_generators()])

    class CartesianProducts(CartesianProductsCategory):
        """
        The category of monoids constructed as Cartesian products of monoids.

        This construction gives the direct product of monoids. See
        :wikipedia:`Direct_product` for more information.
        """
        def extra_super_categories(self):
            """
            A Cartesian product of monoids is endowed with a natural
            group structure.

            EXAMPLES::

                sage: C = Monoids().CartesianProducts()
                sage: C.extra_super_categories()
                [Category of monoids]
                sage: sorted(C.super_categories(), key=str)
                [Category of Cartesian products of semigroups,
                 Category of Cartesian products of unital magmas,
                 Category of monoids]
            """
            return [self.base_category()]

        class ParentMethods:
            @cached_method
            def monoid_generators(self):
                """
                Return the generators of ``self``.

                EXAMPLES::

                    sage: M = Monoids.free([1,2,3])
                    sage: N = Monoids.free(['a','b'])
                    sage: C = cartesian_product([M, N])
                    sage: C.monoid_generators()
                    Family ((F[1], 1), (F[2], 1), (F[3], 1),
                            (1, F['a']), (1, F['b']))

                An example with an infinitely generated group (a better output
                is needed)::

                    sage: N = Monoids.free(ZZ)
                    sage: C = cartesian_product([M, N])
                    sage: C.monoid_generators()
                    Lazy family (gen(i))_{i in The Cartesian product of (...)}
                """
                F = self.cartesian_factors()
                ids = tuple(M.one() for M in F)
                def lift(i, gen):
                    cur = list(ids)
                    cur[i] = gen
                    return self._cartesian_product_of_elements(cur)
                from sage.sets.family import Family

                # Finitely generated
                cat = FiniteEnumeratedSets()
                if all(M.monoid_generators() in cat
                       or isinstance(M.monoid_generators(), (tuple, list)) for M in F):
                    ret = [lift(i, gen) for i,M in enumerate(F) for gen in M.monoid_generators()]
                    return Family(ret)

                # Infinitely generated
                # This does not return a good output, but it is "correct"
                # TODO: Figure out a better way to do things
                from sage.categories.cartesian_product import cartesian_product
                gens_prod = cartesian_product([Family(M.monoid_generators(),
                                                      lambda g: (i, g))
                                               for i,M in enumerate(F)])
                return Family(gens_prod, lift, name="gen")

